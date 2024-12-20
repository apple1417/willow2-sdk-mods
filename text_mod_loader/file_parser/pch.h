#ifndef FILE_PARSER_PCH_H
#define FILE_PARSER_PCH_H

#ifdef _WIN32
#include <winerror.h>
#else
#include <errno.h>
#endif

#ifdef __clang__
// Python, detecting `_MSC_VER`, tries to use `__int64`, which is an MSVC extension
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wlanguage-extension-token"
#endif

#include "Python.h"

#ifdef __clang__
#pragma clang diagnostic pop
#endif

#ifdef __cplusplus

#include <algorithm>
#include <cctype>
#include <charconv>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <ranges>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl/filesystem.h>

// NOLINTNEXTLINE(misc-unused-alias-decls)
namespace py = pybind11;
using namespace pybind11::literals;

#include <pugixml.hpp>

#endif

#endif /* FILE_PARSER_PCH_H */
