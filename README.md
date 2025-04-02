# Wavelet Bench

A video encoding benchmarking tool for wavelet-based video codecs.

## Overview

Wavelet Bench is a benchmarking toolkit designed to evaluate the performance of various video encoders, with a focus on wavelet-based codecs. It provides tools to generate comprehensive metrics including PSNR, SSIM, and XPSNR, allowing for detailed analysis and comparison of different encoding algorithms.

## TODO

- [ ] DSV2 support
- [ ] Dirac support
- [x] x264 support
- [x] Snow support

## Features

- Support for multiple wavelet-based encoders, including:
  - Snow (FFmpeg's wavelet codec)
  - Dirac (BBC's open-source wavelet codec)
  - DSV2 (custom wavelet encoder)
  - X264 (for comparison)
- Automated quality testing across multiple quality levels
- Detailed metrics collection:
  - PSNR (Peak Signal-to-Noise Ratio)
  - SSIM (Structural Similarity Index)
  - XPSNR (Extended PSNR for Y, U, V channels)
  - W-XPSNR (Weighted XPSNR)
- CSV output for easy analysis and visualization
- Performance tracking (encoding time and file size)

## Requirements

- Python 3.13.2+
- FFmpeg (with XPSNR support)
- X264 (optional, for comparison testing)
- Other codec implementations as needed

## Installation

### Dependencies

- [uv](https://github.com/astral-sh/uv/blob/main/README.md), a Python project
  manager
- FFmpeg >= 7.1 (for XPSNR calculations)

### Install Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/username/wavelet-bench.git
   cd wavelet-bench
   ```

2. Mark the scripts as executable:
   ```bash
   cd scripts/
   chmod a+x encode.py
   chmod a+x stats.py
   ```

3. Run the script of your choice:
   ```bash
   ./stats.py --help
   ```

## Usage

### Single Encode Test

To test a single video encode and see detailed metrics:

```bash
./encode.py -i /path/to/video.mp4 -q 30 x264 -- --preset medium
```

Options:
- `-i, --input`: Path to source video file (required)
- `-q, --quality`: Quality/CRF value for the encoder (required)
- `encoder`: Which encoder to use (snow, dsv2, dirac, x264)
- `-b, --out`: Output video filename (optional)
- `encoder_args`: Additional encoder arguments (pass after `--`)

### Batch Testing

For comprehensive testing across multiple quality settings and videos:

```bash
./stats.py -i video1.mp4 video2.mp4 -q "20 30 40 50" x264 -o results.csv -- --preset medium
```

Options:
- `-i, --inputs`: One or more source video files (required)
- `-q, --quality`: Space-separated list of quality values to test (required)
- `encoder`: Which encoder to use (snow, dsv2, dirac, x264)
- `-o, --output`: Output CSV file path (required)
- `-k, --keep`: Keep encoded video files (default is to delete)
- `encoder_args`: Additional encoder arguments (pass after `--`)

## License

See [License](LICENSE) for more info.
