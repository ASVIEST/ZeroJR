# ZeroJR
Дискорд бот для сохранения структуры вашего сервера в файле формата **.pkl**

**На данный момент сохраняются:**
- Название сервера
- Категории
- Голосовые и текстовые каналы
- Ветки в каналах с полным списком пользователей
- Вся история текстовых сообщений
- Все эмодзи сервера

**НЕ подлежат сохранению:**
- Роли
- Любые настройки прав доступа (исключение - флаг **nsfw**)


## Восстановление истории сообщений
Сохранённые текстовые сообщения отправляются в каналы и ветки через вебхук с никнеймом и аватаркой оригинального автора сообщения. В дискорде установлено ограничение для каждого канала по скорости отправки вебхуков (~ 30 сообщений в минуту. https://stackoverflow.com/questions/59117210/discord-webhook-rate-limits), поэтому восстановление истории собщений занимает некоторое время. Будьте готовы 30 минут наблюдать за появлением вашего сервера. Проблема частично решается объединением серии сообщений от одного автора в одно большое (до лимита по символам).



## Инструкция по запуску бота:

1. Добавить файл .env с содержимым вида "TOKEN = {Ваш токен}"
2. Установить зависимости
3. Запустить main.py



## Функции бота:

1. Дампить сервер в .pkl файл
2. Выгружать дамп на существующий Дискорд сервер из .pkl файла
3. Очищать ветки/каналы/категории/эмодзи
4. Выводить забавные сообщения в консоль во время работы



## Консольные команды:

1. **create** {id сервера}
2. **load** {id сервера} {файл с дампом}
3. **clear** {id сервера} all/threads/channels/categories/emojis



## Для безумца, который решит зайти в код:

Бот релизован на нескольких библиотеках, основные функции возможны благодаря:
- discord.py + документация pycorde (https://docs.pycord.dev/en/stable/)
- pickle (https://docs.python.org/3/library/pickle.html)
- dpyConsole (https://github.com/Mihitoko/discord.py-Console?ysclid=m07axn47qg974980974)
- Rich (https://github.com/Textualize/rich?ysclid=m07b3crzoa137533031) - используется для отладки.


Состоит из трёх основных частей:

- **main.py** - CLI

- **builder.py** - Представляет из себя набор классов, каждый из которых отвечает за создание на сервере соответствующих объектов (веток, каналов, категорий и т.д.).

- **record.py** - Является набором классов, которые представляют собой дерево, описывающее сервер discord, которое будет сохранено в памяти. Мы не можем использовать классы Discord т.к оне создают циклические ссылки, а Pickle с ними не дружит и зависает. Каждый класс в record имеет декоратор @dataclass(frozen = True), что делает его неизменяемым и имеющим магические __repr__, __hash__, __init__

- **gen_record.py** - Является генератором объектов из record.py. Это необходимо т.к классы часто имеют довольно большой конструктор из-за большого кол-ва полей у объектов, поэтому необходимо инициализировать множество полей в одном констукторе, что создает необходимость в дополнительных переменных (объекты из record неизменяемы), например могут понадобиться списки, для thread-ов, которые потом придется приводить к tuple и передавать в констуктор. Процесс генерации thread тоже не очень удобный т.к необходимо создать переменную, получить данные из какого-то классы, необходимые для правильной генерации объекта из record, который потом будет добавлен в список. Чтобы решить эту проблему используется модуль gen_record, который по сути реализует шаблон проектирования строитель. В нём содержатся генераторы объектов record, которые сильно упрощают код. Каждый объект генератор позволяет изменять и добавлять необходимые св-ва, а также удобно генерировать вложенные объекты, всё это имеет асинхронный api, поэтому возможно использовать асинхронный код в поддеревьях. В реализации используется модуль `async_chain`, который позволяет делать цепочки асинхронных методов.
Использование `gen_record` довольно простое: берётся объект генератор, например `MessageGen`, инициализируется и затем вызываются (с await) методы, добавляющие значения, например
```py
await MessageGen().with_content("Hello world")
```
Это будет всё так же объект `MessageGen`, чтобы сгенерировать объект из record т.е `record.Message`
нужно вызвать метод `get_result()`
т.е 
```py
await MessageGen().with_content("Hello world").get_result()
```
уже будет типа `record.Message`

- **discord2record.py** - Модуль, осуществляющий преобразование объектов discord в объекты record, используя gen_record для генерации. Содержит класс Converter, который по сути конвертирует соответствующий объект discord в соответствующий объект record. Может быть использован в поддеревьях gen_record, например
```py
await gen.with_subtree(SubtreeGen(something).gen_func)
```
каждый `Converter` должен иметь метод `convert`, который имеет следущий вид:
```py
async def convert(self, gen: SomeGen) -> SomeGen:
    return gen
```
Он принимает на вход нужный генератор, изменяет его и возвращает его обратно.

