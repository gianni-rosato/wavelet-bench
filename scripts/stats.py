#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13.2"
# dependencies = [
#     "argparse>=1.4.0",
# ]
# ///

import argparse
import os
from argparse import Namespace

from bench import CoreVideo, DstVideo, VideoEnc


def write_stats(
    name: str,
    q: int,
    encode_time: float,
    size: int,
    psnr: float,
    ssim: float,
    w_xpsnr: float,
) -> None:
    """
    Write metric stats to a CSV file.
    """

    csv: str = name if name.endswith(".csv") else f"{name}.csv"
    if not os.path.exists(csv):
        with open(csv, "w") as f:
            f.write("q,encode_time,output_filesize,psnr,ssim,wxpsnr\n")
            f.write(
                f"{q},{encode_time:.5f},{size},{psnr:.5f},{ssim:.5f},{w_xpsnr:.5f}\n"
            )
    else:
        with open(csv, "a") as f:
            f.write(
                f"{q},{encode_time:.5f},{size},{psnr:.5f},{ssim:.5f},{w_xpsnr:.5f}\n"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Generate PSNR, SSIM, & XPSNR statistics for a series of video encodes."
    )
    parser.add_argument(
        "-i",
        "--inputs",
        required=True,
        type=str,
        nargs="+",
        help="Path(s) to source video file(s)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        required=True,
        type=str,
        help="List of quality values to test (e.g. 20 30 40 50)",
    )
    parser.add_argument(
        "encoder",
        choices=["snow", "dsv2", "dirac", "x264"],
        type=str,
        help="Which video encoder to use",
    )
    parser.add_argument(
        "-o", "--output", required=True, type=str, help="Path to output CSV file"
    )
    parser.add_argument(
        "-k",
        "--keep",
        default=True,
        action="store_false",
        help="Keep output video files",
    )
    parser.add_argument(
        "encoder_args",
        nargs=argparse.REMAINDER,
        type=str,
        help="Additional encoder arguments (pass these after a '--' delimiter)",
    )

    args: Namespace = parser.parse_args()
    src_pth: list[str] = [p for p in args.inputs]
    quality_list: list[int] = [int(q) for q in args.quality.split()]
    enc: str = args.encoder
    csv_out: str = args.output
    clean: bool = args.keep
    enc_args: list[str] = args.encoder_args

    cumulative_sizes: list[dict[int, int]] = [
        {q: 0 for q in quality_list} for _ in range(len(src_pth))
    ]
    cumulative_times: list[dict[int, float]] = [
        {q: 0.0 for q in quality_list} for _ in range(len(src_pth))
    ]
    cumulative_psnr: list[dict[int, float]] = [
        {q: 0.0 for q in quality_list} for _ in range(len(src_pth))
    ]
    cumulative_ssim: list[dict[int, float]] = [
        {q: 0.0 for q in quality_list} for _ in range(len(src_pth))
    ]
    cumulative_wxpsnr: list[dict[int, float]] = [
        {q: 0.0 for q in quality_list} for _ in range(len(src_pth))
    ]
    i: int = 0

    for src in src_pth:
        s: CoreVideo = CoreVideo(src)
        print(f"Source video: {s.name}")

        print(f"Running encoder at qualities: {quality_list}")
        for q in quality_list:
            print(f"Quality: {q}")

            e: VideoEnc = VideoEnc(s, q, enc, enc_args)
            v: DstVideo = e.encode()
            print(f"Encoded video: {e.dst_pth} (took {e.time:.2f} seconds)")

            v.calculate_psnr_ssim(s)
            v.calculate_xpsnr(s)

            cumulative_times[i][q] = e.time
            cumulative_sizes[i][q] = v.size
            cumulative_psnr[i][q] = v.psnr
            cumulative_ssim[i][q] = v.ssim
            cumulative_wxpsnr[i][q] = v.w_xpsnr

            if clean:
                e.remove_output()
        i += 1

    avg_time: dict[int, float] = {}
    avg_size: dict[int, int] = {}
    avg_psnr: dict[int, float] = {}
    avg_ssim: dict[int, float] = {}
    avg_wxpsnr: dict[int, float] = {}

    for q in quality_list:
        avg_time[q] = sum(cumulative_times[j][q] for j in range(i)) / i
        avg_size[q] = int(sum(cumulative_sizes[j][q] for j in range(i)) / i)
        avg_psnr[q] = sum(cumulative_psnr[j][q] for j in range(i)) / i
        avg_ssim[q] = sum(cumulative_ssim[j][q] for j in range(i)) / i
        avg_wxpsnr[q] = sum(cumulative_wxpsnr[j][q] for j in range(i)) / i
        write_stats(
            csv_out,
            q,
            avg_time[q],
            avg_size[q],
            avg_psnr[q],
            avg_ssim[q],
            avg_wxpsnr[q],
        )


if __name__ == "__main__":
    main()
