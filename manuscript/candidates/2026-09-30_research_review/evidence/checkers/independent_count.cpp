// C++17, standard library only; no parent counting implementation is used.
// Usage: independent_count [seconds [max_nodes]] < literal_table.txt
// Input: n in {4,8,16}, then exactly n*n zero-based decimal integers.
// Fibres are the adjacent labels 2a+x, 2b+y, 2s+z.
// Defaults/caps: 120 seconds, 100000000 entered DFS nodes (root included).
// Zero budgets give unknown, not an exclusion. Unknown counts cover only
// visited complete projections; this program makes no FFF/isotopy claim.
// Small control targets: XOR4 has 8 labelled transversals, XOR8 has 384.

#include <array>
#include <cerrno>
#include <charconv>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <utility>

namespace {

constexpr int max_q = 8;
constexpr int max_pairs = max_q * (max_q - 1) / 2;
constexpr std::uint64_t node_cap = 100000000;
constexpr double seconds_cap = 120.0;

template <typename Integer>
Integer decimal_integer(const std::string& token) {
    Integer value{};
    const char* end = token.data() + token.size();
    const auto result = std::from_chars(token.data(), end, value, 10);
    if (token.empty() || result.ec != std::errc{} || result.ptr != end) {
        throw std::invalid_argument("expected a whole decimal integer: " + token);
    }
    return value;
}

int input_integer() {
    std::string token;
    if (!(std::cin >> token)) {
        throw std::invalid_argument("missing integer in literal table input");
    }
    return decimal_integer<int>(token);
}

struct Limits {
    double seconds = seconds_cap;
    std::uint64_t max_nodes = node_cap;
};

Limits read_limits(int argc, char** argv) {
    if (argc > 3) {
        throw std::invalid_argument("usage: independent_count [seconds [max_nodes]]");
    }
    Limits limits;
    if (argc >= 2) {
        char* end = nullptr;
        errno = 0;
        limits.seconds = std::strtod(argv[1], &end);
        if (end == argv[1] || *end != '\0' || errno == ERANGE ||
            !std::isfinite(limits.seconds) || limits.seconds < 0.0 ||
            limits.seconds > seconds_cap) {
            throw std::invalid_argument("seconds must be finite and in [0,120]");
        }
    }
    if (argc == 3) {
        limits.max_nodes = decimal_integer<std::uint64_t>(argv[2]);
        if (limits.max_nodes > node_cap) {
            throw std::invalid_argument("max_nodes must be in [0,100000000]");
        }
    }
    return limits;
}

struct Base {
    int n = 0;
    int q = 0;
    std::array<std::array<int, max_q>, max_q> quotient{};
    std::array<std::array<int, max_q>, max_q> offset{};
};

Base read_base() {
    Base base;
    base.n = input_integer();
    if (base.n != 4 && base.n != 8 && base.n != 16) {
        throw std::invalid_argument("physical order must be 4, 8, or 16");
    }
    base.q = base.n / 2;
    std::array<std::array<int, 2 * max_q>, 2 * max_q> table{};
    for (int r = 0; r < base.n; ++r) {
        for (int c = 0; c < base.n; ++c) {
            const int s = input_integer();
            if (s < 0 || s >= base.n) {
                throw std::invalid_argument("symbol outside [0,n)");
            }
            table[r][c] = s;
        }
    }
    std::string extra;
    if (std::cin >> extra) {
        throw std::invalid_argument("extra token after literal table: " + extra);
    }
    if (!std::cin.eof()) {
        throw std::invalid_argument("input stream failure");
    }

    for (int a = 0; a < base.n; ++a) {
        std::uint32_t row = 0, column = 0;
        for (int b = 0; b < base.n; ++b) {
            const auto row_bit = std::uint32_t{1} << table[a][b];
            const auto column_bit = std::uint32_t{1} << table[b][a];
            if ((row & row_bit) != 0 || (column & column_bit) != 0) {
                throw std::invalid_argument("physical table is not Latin");
            }
            row |= row_bit;
            column |= column_bit;
        }
    }
    for (int a = 0; a < base.q; ++a) {
        for (int b = 0; b < base.q; ++b) {
            const int s = table[2 * a][2 * b] / 2;
            const int h = table[2 * a][2 * b] % 2;
            base.quotient[a][b] = s;
            base.offset[a][b] = h;
            for (int x = 0; x < 2; ++x) {
                for (int y = 0; y < 2; ++y) {
                    if (table[2 * a + x][2 * b + y] !=
                        2 * s + (x ^ y ^ h)) {
                        throw std::invalid_argument(
                            "table is not binary-fibred in the adjacent labels");
                    }
                }
            }
        }
    }
    for (int a = 0; a < base.q; ++a) {
        std::uint32_t row = 0, column = 0;
        for (int b = 0; b < base.q; ++b) {
            const auto row_bit = std::uint32_t{1} << base.quotient[a][b];
            const auto column_bit = std::uint32_t{1} << base.quotient[b][a];
            if ((row & row_bit) != 0 || (column & column_bit) != 0) {
                throw std::invalid_argument("recovered quotient is not Latin");
            }
            row |= row_bit;
            column |= column_bit;
        }
    }
    return base;
}

struct Pair {
    int first = -1;
    int second = -1;
};

class Counter {
public:
    Counter(const Base& base, Limits limits) : base_(base), limits_(limits) {}

    void run() {
        start_ = Clock::now();
        visit(0);
        seconds_ = elapsed();
    }

    void print() const {
        const bool complete = stop_reason_ == nullptr;
        std::cout << std::setprecision(17)
                  << "{\"status\":\"" << (complete ? "complete" : "unknown")
                  << "\",\"complete\":" << (complete ? "true" : "false")
                  << ",\"counts_scope\":\""
                  << (complete ? "all_projections" : "visited_complete_projections")
                  << "\",\"nphysical\":" << base_.n << ",\"q\":" << base_.q
                  << ",\"totalP\":" << total_p_
                  << ",\"liftable\":" << liftable_
                  << ",\"transvcount\":" << transversals_
                  << ",\"canonical_first_count\":" << transversals_ / 4
                  << ",\"coefficient_rank_histogram\":";
        print_histogram(all_ranks_);
        std::cout << ",\"consistent_rank_histogram\":";
        print_histogram(consistent_ranks_);
        std::cout << ",\"nodes\":" << nodes_ << ",\"seconds\":" << seconds_
                  << ",\"limits\":{\"seconds\":" << limits_.seconds
                  << ",\"max_nodes\":" << limits_.max_nodes << "}"
                  << ",\"stop_reason\":";
        if (complete) {
            std::cout << "null";
        } else {
            std::cout << '\"' << stop_reason_ << '\"';
        }
        std::cout << "}\n";
    }

private:
    using Clock = std::chrono::steady_clock;
    using Histogram = std::array<std::uint64_t, 4 * max_q + 1>;

    const Base& base_;
    Limits limits_;
    std::array<Pair, max_q> row_assignments_{};
    std::array<int, max_q> column_use_{};
    std::array<int, max_q> symbol_use_{};
    Histogram all_ranks_{};
    Histogram consistent_ranks_{};
    std::uint64_t nodes_ = 0;
    std::uint64_t total_p_ = 0;
    std::uint64_t liftable_ = 0;
    std::uint64_t transversals_ = 0;
    Clock::time_point start_{};
    double seconds_ = 0.0;
    const char* stop_reason_ = nullptr;

    double elapsed() const {
        return std::chrono::duration<double>(Clock::now() - start_).count();
    }

    static void print_histogram(const Histogram& histogram) {
        std::cout << '{';
        bool first = true;
        for (std::size_t rank = 0; rank < histogram.size(); ++rank) {
            if (histogram[rank] == 0) {
                continue;
            }
            if (!first) {
                std::cout << ',';
            }
            first = false;
            std::cout << '\"' << rank << "\":" << histogram[rank];
        }
        std::cout << '}';
    }

    void visit(int assigned) {
        if (nodes_ >= limits_.max_nodes) {
            stop_reason_ = "max_nodes";
            return;
        }
        if (elapsed() >= limits_.seconds) {
            stop_reason_ = "seconds";
            return;
        }
        ++nodes_;
        if (assigned == base_.q) {
            count_projection();
            return;
        }

        // Deterministic whole-row MRV: each full projection forces exactly
        // one unordered pair at the chosen row, so it is visited once.
        int best_row = -1;
        int best_size = max_pairs + 1;
        std::array<Pair, max_pairs> best_pairs{};
        for (int a = 0; a < base_.q; ++a) {
            if (row_assignments_[a].first >= 0) {
                continue;
            }
            std::array<Pair, max_pairs> legal{};
            int size = 0;
            for (int b = 0; b < base_.q; ++b) {
                if (column_use_[b] >= 2 || symbol_use_[base_.quotient[a][b]] >= 2) {
                    continue;
                }
                for (int c = b + 1; c < base_.q; ++c) {
                    if (column_use_[c] < 2 && symbol_use_[base_.quotient[a][c]] < 2) {
                        legal[size++] = Pair{b, c};
                    }
                }
            }
            if (size == 0) {
                return;
            }
            if (size < best_size) {
                best_row = a;
                best_size = size;
                best_pairs = legal;
            }
        }
        if (best_row < 0) {
            throw std::logic_error("missing unassigned quotient row");
        }
        for (int i = 0; i < best_size; ++i) {
            const Pair pair = best_pairs[i];
            row_assignments_[best_row] = pair;
            ++column_use_[pair.first];
            ++column_use_[pair.second];
            ++symbol_use_[base_.quotient[best_row][pair.first]];
            ++symbol_use_[base_.quotient[best_row][pair.second]];
            visit(assigned + 1);
            --column_use_[pair.first];
            --column_use_[pair.second];
            --symbol_use_[base_.quotient[best_row][pair.first]];
            --symbol_use_[base_.quotient[best_row][pair.second]];
            row_assignments_[best_row] = Pair{};
            if (stop_reason_ != nullptr) {
                return;
            }
        }
    }

    void count_projection() {
        const int q = base_.q;
        const int variables = 4 * q;
        const int equations = 3 * q;
        const std::uint64_t rhs = std::uint64_t{1} << variables;
        const std::uint64_t coefficients = rhs - 1;
        std::array<std::uint64_t, 3 * max_q> matrix{};
        std::array<std::array<int, 2>, max_q> column_cells{};
        std::array<std::array<int, 2>, max_q> symbol_cells{};
        std::array<int, max_q> column_sizes{}, symbol_sizes{};
        std::array<int, 2 * max_q> offsets{};

        // Cell i=2a+j has interleaved variables x_i at 2i, y_i at 2i+1.
        for (int a = 0; a < q; ++a) {
            const Pair pair = row_assignments_[a];
            matrix[a] = (std::uint64_t{1} << (4 * a)) |
                        (std::uint64_t{1} << (4 * a + 2)) | rhs;
            for (int j = 0; j < 2; ++j) {
                const int b = j == 0 ? pair.first : pair.second;
                const int s = base_.quotient[a][b];
                const int cell = 2 * a + j;
                if (column_sizes[b] >= 2 || symbol_sizes[s] >= 2) {
                    throw std::logic_error("projection exceeded a capacity");
                }
                column_cells[b][column_sizes[b]++] = cell;
                symbol_cells[s][symbol_sizes[s]++] = cell;
                offsets[cell] = base_.offset[a][b];
            }
        }
        for (int a = 0; a < q; ++a) {
            if (column_sizes[a] != 2 || symbol_sizes[a] != 2) {
                throw std::logic_error("complete projection is not a two-plex");
            }
            const int i = column_cells[a][0], j = column_cells[a][1];
            matrix[q + a] = (std::uint64_t{1} << (2 * i + 1)) |
                            (std::uint64_t{1} << (2 * j + 1)) | rhs;
            const int k = symbol_cells[a][0], l = symbol_cells[a][1];
            matrix[2 * q + a] = (std::uint64_t{1} << (2 * k)) |
                               (std::uint64_t{1} << (2 * k + 1)) |
                               (std::uint64_t{1} << (2 * l)) |
                               (std::uint64_t{1} << (2 * l + 1));
            if ((1 ^ offsets[k] ^ offsets[l]) != 0) {
                matrix[2 * q + a] |= rhs;
            }
        }

        // Pivot only coefficient columns; a contradictory augmented zero
        // row affects consistency, never the coefficient rank histogram.
        int rank = 0;
        for (int col = 0; col < variables && rank < equations; ++col) {
            const std::uint64_t bit = std::uint64_t{1} << col;
            int pivot = rank;
            while (pivot < equations && (matrix[pivot] & bit) == 0) {
                ++pivot;
            }
            if (pivot == equations) {
                continue;
            }
            std::swap(matrix[rank], matrix[pivot]);
            for (int row = rank + 1; row < equations; ++row) {
                if ((matrix[row] & bit) != 0) {
                    matrix[row] ^= matrix[rank];
                }
            }
            ++rank;
        }
        ++total_p_;
        ++all_ranks_[rank];
        for (int row = 0; row < equations; ++row) {
            if ((matrix[row] & coefficients) == 0 && (matrix[row] & rhs) != 0) {
                return;
            }
        }
        ++liftable_;
        ++consistent_ranks_[rank];
        const std::uint64_t lifts = std::uint64_t{1} << (variables - rank);
        if (lifts % 4 != 0) {
            throw std::logic_error("lift count violates the free four-bit orbit");
        }
        // At most 100m leaves times 2^32 lifts fits uint64_t. The accepted
        // proof_note.md gives canonical FIRST count = labelled count / 4.
        transversals_ += lifts;
    }
};

}  // namespace

int main(int argc, char** argv) {
    try {
        const Limits limits = read_limits(argc, argv);
        const Base base = read_base();
        Counter counter(base, limits);
        counter.run();
        counter.print();
        return 0;
    } catch (const std::invalid_argument& error) {
        std::cerr << "invalid input: " << error.what() << '\n';
        return 2;
    } catch (const std::exception& error) {
        std::cerr << "counter failure: " << error.what() << '\n';
        return 3;
    }
}
