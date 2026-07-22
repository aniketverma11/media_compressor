import os
import io
import time
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from PIL import Image

from mediacompressor.utils.file_utils import get_file_size_bytes, format_size

@dataclass
class ImageInfo:
    file_path: str
    file_name: str
    file_size_bytes: int
    file_size_str: str
    width: int
    height: int
    format_name: str

@dataclass
class ImageCompressionOptions:
    input_paths: List[str]
    output_dir: str
    output_format: str = "JPEG"  # "JPEG", "PNG", "WEBP"
    quality: int = 80            # 1 to 100
    target_size_kb: Optional[float] = None
    target_percentage: Optional[float] = None
    resize_mode: str = "Original" # "Original", "50%", "75%", "Custom"
    custom_max_dim: Optional[int] = None

@dataclass
class ImageBatchResult:
    success_count: int
    failed_count: int
    total_original_bytes: int
    total_compressed_bytes: int
    space_saved_bytes: int
    overall_ratio_pct: float
    time_taken_sec: float
    file_results: List[Tuple[str, bool, int, int, str]]

class ImageCompressor:
    """Handles single and batch image compression using Pillow."""

    FORMAT_MAP = {
        "JPEG": ("JPEG", ".jpg"),
        "PNG": ("PNG", ".png"),
        "WEBP": ("WEBP", ".webp")
    }

    def probe_image(self, file_path: str) -> Tuple[bool, Optional[ImageInfo], str]:
        """Reads image metadata."""
        if not os.path.exists(file_path):
            return False, None, "File does not exist."

        try:
            with Image.open(file_path) as img:
                w, h = img.size
                fmt = img.format or "UNKNOWN"
                file_size = get_file_size_bytes(file_path)
                info = ImageInfo(
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    file_size_bytes=file_size,
                    file_size_str=format_size(file_size),
                    width=w,
                    height=h,
                    format_name=fmt
                )
                return True, info, ""
        except Exception as e:
            return False, None, f"Cannot open image: {e}"

    def estimate_output_size(self, info: ImageInfo, opts: ImageCompressionOptions) -> Tuple[bool, float, str]:
        """
        Estimates final file size in KB.
        Returns: (is_realistic, estimated_size_kb, warning_msg)
        """
        orig_kb = info.file_size_bytes / 1024.0
        est_kb = orig_kb

        if opts.target_size_kb is not None:
            est_kb = opts.target_size_kb
        elif opts.target_percentage is not None:
            est_kb = orig_kb * (1.0 - (opts.target_percentage / 100.0))
        else:
            # Estimate based on quality and format
            scale_factor = (opts.quality / 100.0) * 0.8
            if opts.output_format == "WEBP":
                scale_factor *= 0.7
            est_kb = orig_kb * scale_factor

        # Unrealistic target check (e.g. asking for 2KB for a 4K image)
        min_feasible_kb = (info.width * info.height) / 100000.0  # rough heuristic
        if est_kb < min_feasible_kb:
            msg = (
                f"Requested target size ({est_kb:.1f} KB) is too low for a {info.width}x{info.height} image. "
                f"Minimum realistic size is around {min_feasible_kb:.1f} KB. Image quality will be severely degraded."
            )
            return False, est_kb, msg

        return True, est_kb, ""

    def compress_single(
        self, file_path: str, opts: ImageCompressionOptions
    ) -> Tuple[bool, int, int, str]:
        """Compresses a single image and returns (success, orig_bytes, compressed_bytes, err_msg)."""
        if not os.path.exists(file_path):
            return False, 0, 0, "File not found."

        try:
            orig_size = get_file_size_bytes(file_path)
            with Image.open(file_path) as img:
                # Convert color modes if saving to JPEG
                fmt_key, ext = self.FORMAT_MAP.get(opts.output_format, ("JPEG", ".jpg"))
                
                if fmt_key == "JPEG" and img.mode in ("RGBA", "P", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode in ("RGBA", "LA"):
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background

                # Resize if requested
                w, h = img.size
                if opts.resize_mode == "50%":
                    w, h = max(1, w // 2), max(1, h // 2)
                    img = img.resize((w, h), Image.LANCZOS)
                elif opts.resize_mode == "75%":
                    w, h = max(1, int(w * 0.75)), max(1, int(h * 0.75))
                    img = img.resize((w, h), Image.LANCZOS)
                elif opts.resize_mode == "Custom" and opts.custom_max_dim:
                    max_dim = opts.custom_max_dim
                    if w > max_dim or h > max_dim:
                        if w >= h:
                            new_w = max_dim
                            new_h = max(1, int(h * (max_dim / w)))
                        else:
                            new_h = max_dim
                            new_w = max(1, int(w * (max_dim / h)))
                        img = img.resize((new_w, new_h), Image.LANCZOS)

                # Output file path construction
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                out_name = f"{base_name}_compressed{ext}"
                out_path = os.path.join(opts.output_dir, out_name)

                # If target size is specified, binary search quality
                target_quality = opts.quality
                if opts.target_size_kb is not None and fmt_key in ("JPEG", "WEBP"):
                    target_bytes = opts.target_size_kb * 1024
                    low_q, high_q = 5, 95
                    best_buf = None
                    
                    for _ in range(6):  # 6 iterations binary search
                        mid_q = (low_q + high_q) // 2
                        buf = io.BytesIO()
                        img.save(buf, format=fmt_key, quality=mid_q, optimize=True)
                        b_size = buf.tell()
                        
                        if b_size <= target_bytes:
                            best_buf = buf
                            low_q = mid_q + 1
                        else:
                            high_q = mid_q - 1
                    
                    if best_buf:
                        with open(out_path, "wb") as f:
                            f.write(best_buf.getvalue())
                        comp_size = os.path.getsize(out_path)
                        return True, orig_size, comp_size, ""

                # Default save
                save_kwargs = {"optimize": True}
                if fmt_key in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = target_quality

                img.save(out_path, format=fmt_key, **save_kwargs)
                comp_size = os.path.getsize(out_path)
                return True, orig_size, comp_size, ""

        except Exception as e:
            return False, 0, 0, str(e)

    def compress_batch(
        self,
        opts: ImageCompressionOptions,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> ImageBatchResult:
        """Compresses multiple images in sequence with progress callbacks."""
        start_time = time.time()
        total_files = len(opts.input_paths)
        success_count = 0
        failed_count = 0
        total_orig = 0
        total_comp = 0
        file_results = []

        for idx, file_path in enumerate(opts.input_paths):
            if cancel_check and cancel_check():
                break

            fname = os.path.basename(file_path)
            if progress_callback:
                progress_callback(idx + 1, total_files, f"Compressing {fname}...")

            ok, orig_b, comp_b, err = self.compress_single(file_path, opts)
            if ok:
                success_count += 1
                total_orig += orig_b
                total_comp += comp_b
                file_results.append((fname, True, orig_b, comp_b, ""))
            else:
                failed_count += 1
                file_results.append((fname, False, 0, 0, err))

        saved = max(0, total_orig - total_comp)
        ratio = ((total_orig - total_comp) / total_orig * 100.0) if total_orig > 0 else 0.0

        return ImageBatchResult(
            success_count=success_count,
            failed_count=failed_count,
            total_original_bytes=total_orig,
            total_compressed_bytes=total_comp,
            space_saved_bytes=saved,
            overall_ratio_pct=ratio,
            time_taken_sec=time.time() - start_time,
            file_results=file_results
        )
