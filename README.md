# LlamaTerm
LlamaTerm is a simple CLI utility that allows to use local LLM models easily and with some additional features.
> :warning: Currently this project supports models that use ChatML format or something similar. Use for example [Gemma-2](https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/tree/main) or [Phi-3](https://huggingface.co/bartowski/Phi-3.1-mini-4k-instruct-GGUF/tree/main) GGUFs.

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
1) Rename `example-<model_name>.env` to `.env`
2) Modify the `.env` so that the model path corresponds (you may also need to edit `EOS` and `PREFIX_TEMPLATE` if it's a non-standard model)
3) If you need **syntax highlighting** for code and markdown, then set `REAL_TIME=0` in the `.env`. Note that you will lose real time output generation.
4) Install python dependencies with `pip install -r requirements.txt`

## Run
Run LlamaTerm by adding the project directory to the `PATH` and then running `llamaterm`.

Alternatively you can just run `./llamaterm` from the project directory.

## Models supported out of the box
For the following models you will just need to rename the corresponding example `example-*.env` file to `.env` and set the `MODEL_PATH` field in the `.env`:
* [Gemma-2 Instruct 9B](https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/tree/main) (🔥 **BEST OVERALL**)
* [Phi-3 Instruct Mini](https://huggingface.co/bartowski/Phi-3.1-mini-4k-instruct-GGUF/tree/main) (🍃 **BEST EFFICIENCY**)
* [LLama-3 Instruct 8B](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/tree/main)

All the other models that have a prompt template similar to ChatML are supported but you will need to customize some fields like `PREFIX_TEMPLATE`, `EOS` etc... in the `.env`.
