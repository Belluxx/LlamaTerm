# LlamaTerm
LlamaTerm is a simple CLI utility that allows to use local LLM models easily and with additional features.

## Preview
### Basic usage:
<img src="https://raw.githubusercontent.com/Belluxx/LlamaTerm/main/static/example1.gif" height="300" />

### Injecting file content:
<img src="https://raw.githubusercontent.com/Belluxx/LlamaTerm/main/static/example2.gif" height="300" />

## Features
- Give local files to the model using square brackets\
`User: Can you explain the code in [helloworld.c] please?`
- More coming soon

## Setup
You can setup LLamaTerm by:
1) Rename `example.env` to `.env`
2) Modify `.env` so that the model path corresponds (you may also need to edit `EOS` and `PREFIX_TEMPLATE`)
3) Install python dependencies with `pip install -r requirements.txt`

## Run
Run LlamaTerm by adding the project directory to the `PATH` and then running `llamaterm`

## Models supported
For now only Zephyr is supported\
Recommended: [**Zephyr Beta 7B GGUF**](https://huggingface.co/TheBloke/zephyr-7B-beta-GGUF/tree/main)