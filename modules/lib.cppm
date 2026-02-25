#ifndef COVERAGE

#define export export

module;

export module lib;

import std;

#else

#define export
#include <string>

#endif

export auto greet() -> std::string { return "Hello, World!"; }
