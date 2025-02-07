#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <stdexcept>
#include <utility>
#include <vector>
#include "zlib.h"

using std::int16_t;
using std::int32_t;
using std::int64_t;
using std::int8_t;
using std::size_t;
using std::uint16_t;
using std::uint32_t;
using std::uint64_t;
using std::uint8_t;

namespace {

const constexpr auto OUTPUT_BUFFER_SIZE = 0x1000;

std::pair<size_t, size_t> evalulate(const std::filesystem::path& input_file,
                                    std::span<const uint8_t> zdict) {
    std::ifstream input{input_file, std::ios::binary};
    if (input.fail()) {
        throw std::runtime_error("couldnt open input");
    }

    z_stream template_stream{.zalloc = Z_NULL, .zfree = Z_NULL, .opaque = Z_NULL};

    if (deflateInit(&template_stream, Z_BEST_COMPRESSION) != Z_OK) {
        throw std::runtime_error("failed to init zlib");
    }
    deflateSetDictionary(&template_stream, zdict.data(), zdict.size());

    size_t compressed_size = 0;
    size_t decompressed_size = 0;

    std::vector<uint8_t> output(OUTPUT_BUFFER_SIZE);

    do {
        uint16_t replacement_size{};
        input.read(reinterpret_cast<char*>(&replacement_size), sizeof(replacement_size));
        if (input.eof()) {
            break;
        }

        std::vector<uint8_t> replacement(replacement_size);
        input.read(reinterpret_cast<char*>(replacement.data()), replacement_size);
        if (input.eof()) {
            break;
        }

        if (input.fail()) {
            throw std::runtime_error("io failure");
        }

        z_stream strm;
        deflateCopy(&strm, &template_stream);

        strm.avail_in = replacement_size;
        strm.next_in = replacement.data();
        strm.avail_out = OUTPUT_BUFFER_SIZE;
        strm.next_out = output.data();

        if (deflate(&strm, Z_FINISH) != Z_STREAM_END) {
            deflateEnd(&strm);
            throw std::runtime_error("deflate failure");
        }

        decompressed_size += replacement_size;
        compressed_size += OUTPUT_BUFFER_SIZE - strm.avail_out;

        deflateEnd(&strm);

    } while (!input.eof());

    deflateEnd(&template_stream);

    return {compressed_size, decompressed_size};
}

}  // namespace

#ifndef FUZZ_TARGET

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::printf("usage: eval <zdict file>\n");
        return 1;
    }

    std::filesystem::path zdict{argv[1]};
    auto zdict_size = std::filesystem::file_size(zdict);
    std::ifstream zdict_stream(zdict, std::ios::binary);

    std::vector<uint8_t> zdict_buffer(zdict_size);
    if (!zdict_stream.read(reinterpret_cast<char*>(zdict_buffer.data()),
                           (std::streamsize)zdict_size)) {
        throw std::runtime_error("failed to read dict");
    }

    auto [compressed, decompressed] = evalulate("exodus.bin", zdict_buffer);
    std::printf("%s: %zd/%zd\n", argv[1], compressed, decompressed);

    return 0;
}

#else

// NOLINTNEXTLINE(readability-identifier-naming)
extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    // Require a full dictionary's worth
    if (size < 0x8000) {
        return -1;
    }

    auto [compressed, decompressed] = evalulate("exodus.bin", {data, size});

    if (compressed < FUZZ_TARGET) {
        throw std::runtime_error("better dict");
    }

    return 0;
}

#endif
