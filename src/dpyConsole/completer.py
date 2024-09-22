from functools import singledispatch
from utils import PickleFilePath
from pathlib import Path
import pickle
import discord
import shlex
import inspect
import asyncio
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class CompleteInfo:
    console: 'Console'
    bot: discord.Bot
    loop: asyncio.AbstractEventLoop

Func = Callable[..., Any]
def dispatch_by_type(fn: Func):
    registry = {}
    def wrapper[T](typ: T, *args, **kwargs):
        if typ in registry:
            return registry[typ](*args, **kwargs)
        else:
            return fn(*args, **kwargs)
    
    def register[T](typ: T):
        def decorator[T](overload: Func):
            registry[typ] = overload
            return overload
        return decorator
    
    wrapper.register = register
    return wrapper



# Type completes

@dispatch_by_type
def get_type_completes(x, complete_info: CompleteInfo) -> list[str]:
    return []

@get_type_completes.register(PickleFilePath)
def _(s: str, _):
    completes = []
    for file in Path.cwd().glob(f"{s.strip()}*"):
        if file.is_dir(): continue
        with open(file, "br") as f:
            data = f.read()
            if data.startswith(b"DPKL") and data.endswith(pickle.STOP):
                rel = file.relative_to(Path.cwd())
                completes.append(str(rel))
    return completes

@get_type_completes.register(discord.Guild)
def _(s: str, complete_info: CompleteInfo):
    async def get_completes() -> list[str]:
        completes = []
        for guild in complete_info.bot.guilds:
            name = guild.name
            if name.startswith(s):
                completes.append(name)
        return completes
    task = asyncio.run_coroutine_threadsafe(get_completes(), complete_info.loop)
    while not task.done(): pass
    return task.result()

def get_keyword_completes(x: str, complete_info: CompleteInfo):
    completes = []
    for command in complete_info.console.__commands__.keys():
        if command.startswith(x):
            completes.append(command)
    return completes

def get_completes(s: str, complete_info: CompleteInfo):
    try:
        console_in = shlex.split(s)
    except:
        return []
    if len(console_in) == 0: return get_keyword_completes("", complete_info)
    completes = []
    offset = s[-1].startswith((' ','\t'))
    if len(console_in) + offset == 1:
        completes = get_keyword_completes(console_in[0], complete_info)
    else:
        commands = complete_info.console.__commands__
        if console_in[0] not in commands:
            return []
        command = commands[console_in[0]]
        signature = inspect.signature(command.__callback__)
        
        if len(console_in) + offset - 1 > len(signature.parameters):
            return []
        
        params = tuple(signature.parameters.values())
        last_param = params[len(console_in) - 2 + offset]
        if not last_param:
            return []
        
        typ = last_param.annotation
        if offset:
            completes = get_type_completes(typ, "", complete_info)
        else:
            completes = get_type_completes(typ, console_in[-1], complete_info)
    return completes

from prompt_toolkit.completion import Completer, Completion
class ConsoleCompleter(Completer):
    def __init__(self, complete_info: CompleteInfo):
        self.complete_info = complete_info
    def get_completions(self, document, complete_event):
        line = document.current_line_before_cursor
        for complete in get_completes(line, self.complete_info):
            yield Completion(complete, start_position=-len(document.get_word_before_cursor()))