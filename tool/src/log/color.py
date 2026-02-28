from src.log.const import Color, ColorMap, Field, Level

FIELD_MAP: ColorMap[Field] = {
    Field.NAME: Color.DIM,
    Field.ASCTIME: Color.BLUE,
    Field.MSECS: Color.BRIGHT_CYAN,
    Field.CREATED: Color.MAGENTA,
    Field.RELATIVECREATED: Color.BRIGHT_MAGENTA,
    Field.FILENAME: Color.BLUE | Color.ITALIC,
    Field.PATHNAME: Color.BRIGHT_BLUE | Color.ITALIC,
    Field.MODULE: Color.YELLOW,
    Field.FUNCNAME: Color.BLUE | Color.ITALIC,
    Field.LINENO: Color.MAGENTA | Color.DIM,
    Field.LEVELNAME: Color.WHITE,
    Field.LEVELNO: Color.BRIGHT_WHITE,
    Field.MESSAGE: Color.BRIGHT_GREEN,
    Field.TASKNAME: Color.GREEN | Color.ITALIC,
    Field.PROCESSNAME: Color.YELLOW,
    Field.PROCESS: Color.BRIGHT_YELLOW,
    Field.THREADNAME: Color.GREEN,
    Field.THREAD: Color.BRIGHT_GREEN,
}

LEVEL_MAP: ColorMap[Level] = {
    Level.DEBUG: Color.GREEN,
    Level.INFO: Color.BLUE,
    Level.WARNING: Color.YELLOW,
    Level.ERROR: Color.RED,
    Level.CRITICAL: Color.MAGENTA,
}
