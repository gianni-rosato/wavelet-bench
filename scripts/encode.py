#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13.2"
# dependencies = [
#     "argparse>=1.4.0",
# ]
# ///

import argparse
from argparse import Namespace
from bench import CoreVideo, DstVideo, VideoEnc


def main():
    parser = argparse.ArgumentParser(
        description="Generate PSNR, SSIM, & XPSNR statistics for a video encode."
    )
    parser.add_argument(
        "-i", "--input", required=True, type=str, help="Path to source video file"
    )
    parser.add_argument(
        "-q",
        "--quality",
        required=True,
        type=int,
        help="Desired CRF value for the encoder",
    )
    parser.add_argument(
        "encoder",
        choices=["snow", "dsv2", "dirac", "x264"],
        type=str,
        help="Which video encoder to use",
    )
    parser.add_argument("-b", "--out", type=str, help="Output video file name")
    parser.add_argument(
        "encoder_args",
        nargs=argparse.REMAINDER,
        type=str,
        help="Additional encoder arguments (pass these after a '--' delimiter)",
    )

    args: Namespace = parser.parse_args()
    src_pth: str = args.input
    dst_pth: str = args.out
    q: int = args.quality
    enc: str = args.encoder
    enc_args: list[str] = args.encoder_args

    s: CoreVideo = CoreVideo(src_pth)
    print(f"Source video: {s.name}")

    print(f"Running encoder at Q{q}")
    e: VideoEnc = VideoEnc(s, q, enc, enc_args, dst_pth)
    v: DstVideo = e.encode()
    print(f"Encoded video: {e.dst_pth} (took {e.time:.2f} seconds)")

    v.calculate_psnr_ssim(s)
    v.print_psnr_ssim()
    v.calculate_xpsnr(s)
    v.print_xpsnr()

    if not dst_pth:
        e.remove_output()
        print("Discarded encoded video")


if __name__ == "__main__":
    main()
