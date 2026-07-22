import os
import re
import json
import time
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from mediacompressor.utils.file_utils import get_file_size_bytes, format_size

@dataclass
class VideoInfo:
    file_path: str
    file_name: str
    file_size_bytes: int
    file_size_str: str
    width: int
    height: int
    duration_sec: float
    fps: float
    bitrate_kbps: float
    codec_name: str
    audio_codec: Optional[str] = None

@dataclass
class CompressionOptions:
    input_path: str
    output_path: str
    target_size_mb: Optional[float] = None
    target_percentage: Optional[float] = None
    resolution_scale: str = "Original"  # "Original", "1080p", "720p", "480p", "360p"
    fps_choice: str = "Original"        # "Original", "60", "30", "24", "15"
    video_codec: str = "H.264"          # "H.264", "H.265", "AV1"
    audio_bitrate_kbps: int = 128

@dataclass
class CompressionResult:
    success: bool
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio_pct: float
    time_taken_sec: float
    error_message: str = ""

class VideoCompressor:
    """Handles video metadata probing, bitrate estimation, and FFmpeg transcoding."""

    CODEC_MAP = {
        "H.264": "libx264",
        "H.265": "libx265",
        "AV1": "libsvtav1"
    }

    RESOLUTION_MAP = {
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "480p": (854, 480),
        "360p": (640, 360)
    }

    def __init__(self, ffmpeg_path: str, ffprobe_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path or ffmpeg_path

    def probe_video(self, file_path: str) -> Tuple[bool, Optional[VideoInfo], str]:
        """Probes video metadata using ffprobe or ffmpeg."""
        if not os.path.exists(file_path):
            return False, None, "File does not exist."

        file_size = get_file_size_bytes(file_path)
        file_name = os.path.basename(file_path)

        # Try ffprobe json
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(res.stdout)
            
            format_data = data.get("format", {})
            duration = float(format_data.get("duration", 0))
            bitrate = float(format_data.get("bit_rate", 0)) / 1000.0 if format_data.get("bit_rate") else 0

            width = 0
            height = 0
            fps = 30.0
            v_codec = "unknown"
            a_codec = None

            for stream in data.get("streams", []):
                st_type = stream.get("codec_type")
                if st_type == "video" and width == 0:
                    width = int(stream.get("width", 0))
                    height = int(stream.get("height", 0))
                    v_codec = stream.get("codec_name", "unknown")
                    # FPS calculation
                    r_frame_rate = stream.get("r_frame_rate", "30/1")
                    if "/" in r_frame_rate:
                        num, den = r_frame_rate.split("/")
                        if float(den) > 0:
                            fps = float(num) / float(den)
                elif st_type == "audio" and not a_codec:
                    a_codec = stream.get("codec_name")

            if bitrate == 0 and duration > 0:
                bitrate = (file_size * 8.0 / duration) / 1000.0

            info = VideoInfo(
                file_path=file_path,
                file_name=file_name,
                file_size_bytes=file_size,
                file_size_str=format_size(file_size),
                width=width,
                height=height,
                duration_sec=duration,
                fps=fps,
                bitrate_kbps=bitrate,
                codec_name=v_codec,
                audio_codec=a_codec
            )
            return True, info, ""

        except Exception as e:
            # Fallback to parsing `ffmpeg -i` output
            try:
                cmd_ff = [self.ffmpeg_path, "-i", file_path]
                res_ff = subprocess.run(cmd_ff, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                output = res_ff.stderr

                duration = 0.0
                width = 1920
                height = 1080
                fps = 30.0
                bitrate = 0.0
                v_codec = "h264"

                # Duration: 00:01:23.45
                dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
                if dur_match:
                    h, m, s = float(dur_match.group(1)), float(dur_match.group(2)), float(dur_match.group(3))
                    duration = h * 3600 + m * 60 + s

                # Bitrate: 2500 kb/s
                br_match = re.search(r"bitrate:\s*(\d+)\s*kb/s", output)
                if br_match:
                    bitrate = float(br_match.group(1))

                # Resolution: 1920x1080
                res_match = re.search(r"Video:\s*(\w+)[^,\n]*,[^,\n]*,?\s*(\d{3,4})x(\d{3,4})", output)
                if res_match:
                    v_codec = res_match.group(1)
                    width = int(res_match.group(2))
                    height = int(res_match.group(3))

                if bitrate == 0 and duration > 0:
                    bitrate = (file_size * 8.0 / duration) / 1000.0

                info = VideoInfo(
                    file_path=file_path,
                    file_name=file_name,
                    file_size_bytes=file_size,
                    file_size_str=format_size(file_size),
                    width=width,
                    height=height,
                    duration_sec=duration,
                    fps=fps,
                    bitrate_kbps=bitrate,
                    codec_name=v_codec
                )
                return True, info, ""
            except Exception as ex:
                return False, None, f"Failed to probe video: {e} | Fallback: {ex}"

    def estimate_bitrate_and_feasibility(
        self, info: VideoInfo, opts: CompressionOptions
    ) -> Tuple[bool, float, float, str, float]:
        """
        Calculates target bitrate (kbps) & target size (MB).
        Returns: (is_achievable, target_video_bitrate_kbps, target_size_mb, explanation, suggested_size_mb)
        """
        if info.duration_sec <= 0:
            return False, 0.0, 0.0, "Cannot estimate for video with unknown duration.", 0.0

        # Calculate target size MB
        orig_mb = info.file_size_bytes / (1024.0 * 1024.0)
        target_mb = orig_mb

        if opts.target_size_mb is not None:
            target_mb = opts.target_size_mb
        elif opts.target_percentage is not None:
            target_mb = orig_mb * (1.0 - (opts.target_percentage / 100.0))

        target_bits = target_mb * 8.0 * 1024.0 * 1024.0
        total_bitrate_kbps = target_bits / (info.duration_sec * 1000.0)
        video_bitrate_kbps = total_bitrate_kbps - opts.audio_bitrate_kbps

        # Minimum sensible video bitrate thresholds depending on target resolution
        target_res = opts.resolution_scale
        w, h = info.width, info.height
        if target_res in self.RESOLUTION_MAP:
            w, h = self.RESOLUTION_MAP[target_res]

        min_bitrate_map = {
            (1920, 1080): 600.0,
            (1280, 720): 350.0,
            (854, 480): 200.0,
            (640, 360): 120.0
        }
        
        # Determine closest resolution threshold
        min_video_bitrate = 150.0
        for (rw, rh), m_br in min_bitrate_map.items():
            if h >= rh - 50:
                min_video_bitrate = m_br
                break

        # Adjust threshold for H.265 / AV1 efficiency
        if opts.video_codec == "H.265":
            min_video_bitrate *= 0.75
        elif opts.video_codec == "AV1":
            min_video_bitrate *= 0.60

        if video_bitrate_kbps < min_video_bitrate:
            min_total_br = min_video_bitrate + opts.audio_bitrate_kbps
            suggested_mb = (min_total_br * 1000.0 * info.duration_sec) / (8.0 * 1024.0 * 1024.0)
            msg = (
                f"Requested size ({target_mb:.2f} MB) requires a video bitrate of {video_bitrate_kbps:.1f} kbps, "
                f"which is below the minimum threshold ({min_video_bitrate:.1f} kbps) for acceptable video quality. "
                f"The output will look severely degraded or pixelated."
            )
            return False, video_bitrate_kbps, target_mb, msg, suggested_mb

        return True, video_bitrate_kbps, target_mb, "Achievable target size and quality.", target_mb

    def compress_video(
        self,
        info: VideoInfo,
        opts: CompressionOptions,
        progress_callback: Optional[Callable[[float, str, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> CompressionResult:
        """
        Executes FFmpeg compression with real-time stderr progress parsing.
        progress_callback(percent, speed_str, eta_str)
        """
        start_time = time.time()
        
        # Calculate target bitrate
        is_achievable, video_br_kbps, target_mb, msg, suggested_mb = self.estimate_bitrate_and_feasibility(info, opts)
        if video_br_kbps <= 50:
            video_br_kbps = 100.0

        v_codec = self.CODEC_MAP.get(opts.video_codec, "libx264")

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", opts.input_path,
            "-c:v", v_codec,
            "-b:v", f"{int(video_br_kbps)}k",
            "-maxrate", f"{int(video_br_kbps * 1.5)}k",
            "-bufsize", f"{int(video_br_kbps * 2.0)}k",
            "-preset", "medium"
        ]

        # Resolution scaling
        vf_filters = []
        if opts.resolution_scale in self.RESOLUTION_MAP:
            rw, rh = self.RESOLUTION_MAP[opts.resolution_scale]
            vf_filters.append(f"scale={rw}:-2")

        # FPS scaling
        if opts.fps_choice != "Original" and opts.fps_choice.isdigit():
            fps_val = int(opts.fps_choice)
            cmd.extend(["-r", str(fps_val)])

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        # Audio settings
        cmd.extend(["-c:a", "aac", "-b:a", f"{opts.audio_bitrate_kbps}k"])
        cmd.append(opts.output_path)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            time_pattern = re.compile(r"time=(\d+):(\d+):(\d+\.\d+)")
            speed_pattern = re.compile(r"speed=\s*([\d\.]+)x")
            fps_pattern = re.compile(r"fps=\s*([\d\.]+)")

            while True:
                if cancel_check and cancel_check():
                    process.terminate()
                    process.wait()
                    if os.path.exists(opts.output_path):
                        try:
                            os.remove(opts.output_path)
                        except OSError:
                            pass
                    return CompressionResult(
                        success=False,
                        original_size_bytes=info.file_size_bytes,
                        compressed_size_bytes=0,
                        compression_ratio_pct=0,
                        time_taken_sec=time.time() - start_time,
                        error_message="Compression cancelled by user."
                    )

                line = process.stderr.readline() if process.stderr else ""
                if not line and process.poll() is not None:
                    break

                if line and info.duration_sec > 0:
                    t_match = time_pattern.search(line)
                    s_match = speed_pattern.search(line)
                    f_match = fps_pattern.search(line)

                    if t_match:
                        h = float(t_match.group(1))
                        m = float(t_match.group(2))
                        s = float(t_match.group(3))
                        curr_sec = h * 3600 + m * 60 + s
                        pct = min(100.0, (curr_sec / info.duration_sec) * 100.0)

                        speed_str = f"{s_match.group(1)}x" if s_match else (f"{f_match.group(1)} fps" if f_match else "1.0x")
                        
                        # ETA calculation
                        elapsed = time.time() - start_time
                        if pct > 0:
                            total_est = (elapsed / pct) * 100.0
                            rem_sec = max(0.0, total_est - elapsed)
                            eta_str = f"{int(rem_sec // 60):02d}:{int(rem_sec % 60):02d}"
                        else:
                            eta_str = "--:--"

                        if progress_callback:
                            progress_callback(pct, speed_str, eta_str)

            process.wait()
            time_taken = time.time() - start_time

            if process.returncode == 0 and os.path.exists(opts.output_path):
                compressed_size = get_file_size_bytes(opts.output_path)
                orig_size = info.file_size_bytes
                ratio = max(0.0, ((orig_size - compressed_size) / orig_size) * 100.0) if orig_size > 0 else 0.0
                
                return CompressionResult(
                    success=True,
                    original_size_bytes=orig_size,
                    compressed_size_bytes=compressed_size,
                    compression_ratio_pct=ratio,
                    time_taken_sec=time_taken
                )
            else:
                stderr_text = process.stderr.read() if process.stderr else ""
                return CompressionResult(
                    success=False,
                    original_size_bytes=info.file_size_bytes,
                    compressed_size_bytes=0,
                    compression_ratio_pct=0,
                    time_taken_sec=time_taken,
                    error_message=f"FFmpeg exit code {process.returncode}: {stderr_text[:200]}"
                )

        except Exception as e:
            return CompressionResult(
                success=False,
                original_size_bytes=info.file_size_bytes,
                compressed_size_bytes=0,
                compression_ratio_pct=0,
                time_taken_sec=time.time() - start_time,
                error_message=str(e)
            )
