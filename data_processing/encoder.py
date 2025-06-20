#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

from memvid import MemvidEncoder
from memvid.config import get_default_config, get_codec_parameters

def main():
    parser = argparse.ArgumentParser(
        description="Encode markdown files into a MemVid memory video and index."
    )
    parser.add_argument(
        "--input-dir",
        default="data/accident-reports-15-markdown",
        help="Directory containing markdown files"
    )
    parser.add_argument(
        "--output-dir",
        default="data/current",
        help="Directory to store encoded outputs"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory not found: {input_dir}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    md_files = list(input_dir.rglob("*.md"))
    num_files = len(md_files)
    if num_files == 0:
        print(f"No markdown files found in {input_dir}")
        return 1

    # Configure encoder for good data retention
    config = get_default_config()
    config["chunking"]["chunk_size"] = 2048
    config["chunking"]["overlap"] = 64
    config["index"]["type"] = "IVF"
    # codec remains default for compression

    encoder = MemvidEncoder(config)

    # Read and add each markdown file
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        encoder.add_text(text)

    # Determine output file paths
    actual_codec = encoder.config.get("codec")
    video_ext = get_codec_parameters(actual_codec).get("video_file_type", "mp4")
    video_path = output_dir / f"encoded_memory.{video_ext}"
    index_json = output_dir / "encoded_memory_index.json"

    # Build memory video and index (JSON + FAISS)
    encoder.build_video(str(video_path), str(index_json))

    index_faiss = output_dir / "encoded_memory_index.faiss"

    # Print summary
    print(f"Processed {num_files} markdown files.")
    print(f"Video file: {video_path}")
    print(f"JSON index file: {index_json}")
    print(f"FAISS index file: {index_faiss}")
    return 0

if __name__ == "__main__":
    exit(main())