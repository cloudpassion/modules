from os import getcwd

from omegaconf import OmegaConf

try:
    settings = OmegaConf.load('settings.yml')
except FileNotFoundError:
    settings = OmegaConf
    print(f'{getcwd()}/settings.yml not found')

try:
    secrets = OmegaConf.load('.secrets.yml')
except FileNotFoundError:
    secrets = OmegaConf
    print(f'{getcwd()}/.secrets.yml not found')

