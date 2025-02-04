import argparse
from collections import defaultdict
from itertools import permutations

from tqdm import tqdm


def generate_symbols(excluded_digit: str) -> set[str]:
    """
    Generate a set of digits 0-9 excluding the specified digit.
    
    Args:
        excluded_digit: The digit to exclude (cannot be '0', '2', or '5').
        
    Returns:
        Set of digits excluding the specified digit.

    Raises:
        ValueError: Excluded digit cannot be '0', '2', or '5'.
    """
    if excluded_digit in {'0', '2', '5'}:
        raise ValueError("Excluded digit cannot be '0', '2', or '5'")
    
    return set(str(i) for i in range(10)) - {excluded_digit}


def generate_permutations(symbols: set[str]) -> list[int]:
    """
    Generate all possible 9-digit numbers from permutations of the given symbols.
    
    Args:
        symbols: Set of digits to permute.
        
    Returns:
        List of all numbers that can be formed.
    """
    return [int(''.join(p)) for p in permutations(symbols, 9)]


def count_divisors(n: int, divisor_counts: dict[int, int]) -> None:
    """
    Count divisors for a number, updating the counts in the provided dictionary.
    
    Args:
        n: Number to find divisors for.
        divisor_counts: Dictionary to update with divisor counts.
    """
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            divisor_counts[i] += 1

            # Avoid counting perfect square divisors twice
            if i != n // i:  
                divisor_counts[n // i] += 1


def build_divisor_counts(numbers: list[int]) -> dict[int, int]:
    """
    Build a dictionary of divisor counts for all numbers in the list.
    
    Args:
        numbers: List of numbers to analyze.
        
    Returns:
        Dictionary mapping divisors to their frequency.
    """
    divisor_counts = defaultdict(int)

    for num in tqdm(numbers, desc="Counting divisors"):
        count_divisors(num, divisor_counts)
        
    return divisor_counts


def find_numbers_with_divisor(numbers: list[int], divisor: int) -> list[str]:
    """
    Find all numbers from the permutations that have the given divisor,
    returning them as 9-digit padded strings.
    
    Args:
        numbers: List of permuted numbers to check.
        divisor: Divisor to test for.
        
    Returns:
        List of 9-digit padded strings representing numbers divisible by divisor.
    """
    return [f"{num:09}" for num in numbers if num % divisor == 0]


def check_digit_positions(numbers: list[str], symbols: set[str]) -> list[set[str]]:
    """
    For each position 0-8, find which digits from our symbol set appear in that position
    across all the given numbers.
    
    Args:
        numbers: List of 9-digit strings to analyze.
        symbols: Set of digits we're looking for.
        
    Returns:
        List of sets, where each set contains the digits found in that position.
    """
    position_digits = [set() for _ in range(9)]

    for num in numbers:
        for pos, digit in enumerate(num):
            if digit in symbols:
                position_digits[pos].add(digit)

    return position_digits


def get_row_constraints() -> dict[int, tuple[int, str] | None]:
    """
    Get the constraints for each row.
    
    Returns:
        Dictionary mapping row index to (position, digit) constraints.
        Row 4's constraint is None, representing no constraint.
    """
    return {
        0: (7, '2'),
        1: (8, '5'),
        2: (1, '2'),
        3: (2, '0'),
        4: None,
        5: (3, '2'),
        6: (4, '0'),
        7: (5, '2'),
        8: (6, '5')
    }


def get_box_constraints() -> dict[int, list[tuple[int, int, str]]]:
    """Returns box-related constraints derived from the row constraints.
    
    Each constraint is represented as (row, col, digit) where:
    - row and col are the position in the 9x9 grid, and
    - digit is the required digit at that position.
    
    Returns:
        Dictionary mapping box numbers (0-8) to lists of constraints within that box.
        Every box number (0-8) will have an entry, though some may have empty lists.
    """
    # Initialize all boxes with empty constraint lists
    box_constraints = {i: [] for i in range(9)}
    
    row_constraints = get_row_constraints()
    for row, constraint in row_constraints.items():
        if constraint is None:
            continue
        col, digit = constraint
        # Calculate which box this position belongs to
        box_num = (row // 3) * 3 + (col // 3)
        box_constraints[box_num].append((row, col, digit))
    
    return box_constraints


def check_box_constraints(num: str, row: int) -> bool:
    """Checks if a number violates any box constraints based on its row placement.
    
    Args:
        num: 9-digit string representing the number.
        row: The row where this number would be placed (0-8).
    
    Returns:
        True if the number satisfies all box constraints for its row.
    """
    box_constraints = get_box_constraints()
    box_row = row // 3  # Which horizontal third of the grid we're in (0, 1, or 2)
    
    # Check each box that this row intersects with
    for box_col in range(3):
        box_num = box_row * 3 + box_col
        box_start_col = box_col * 3
        
        # Get the three digits from our number that would go in this box
        box_section = set(num[box_start_col:box_start_col + 3])
        
        # Check if any required digits in this box appear in wrong positions
        for r, c, digit in box_constraints[box_num]:
            if r != row and digit in box_section:
                return False
    
    return True


def find_valid_row_for_number(
    num: str, 
    constraints: dict[int, tuple[int, str] | None]
) -> int | None:
    """Determines which row (if any) a number is valid for in the Sudoku grid.

    A number is valid for:
    - Row 4 if it matches no positional constraints and satisfies box constraints.
    - A specific row if it matches exactly that row's constraint and satisfies box constraints.
    - No row if it matches multiple constraints or violates box constraints.

    Args:
        num: A 9-digit string representing the number to check.
        constraints: Dictionary mapping row indices to (position, digit) constraints.

    Returns:
        The valid row index (0-8), or None if the number is invalid for all rows.
    """
    matching_rows = []
    
    # Check which row constraints this number matches
    for row_idx, constraint in constraints.items():
        if constraint is None:
            continue
        pos, digit = constraint
        if num[pos] == digit:
            # Only add the row if it also satisfies box constraints
            if check_box_constraints(num, row_idx):
                matching_rows.append(row_idx)
    
    if len(matching_rows) > 1:
        return None  # Number matches multiple rows
    elif len(matching_rows) == 1:
        return matching_rows[0]  # Number matches exactly one row
    
    # No matching constraints - check if it can go in row 4
    if check_box_constraints(num, 4):
        return 4
    
    return None  # Violates box constraints for all possible placements


def categorize_numbers_by_row(numbers: list[str]) -> dict[int, list[str]]:
    """Categorizes numbers based on which row they can validly appear in.
    
    Numbers must satisfy both position constraints and box constraints to be
    considered valid for a row.

    Args:
        numbers: List of candidate numbers as 9-digit strings.

    Returns:
        Dictionary mapping row indices to lists of valid numbers for that row.
    """
    constraints = get_row_constraints()
    valid_numbers_by_row = defaultdict(list)
    
    for num in numbers:
        valid_row = find_valid_row_for_number(num, constraints)

        if valid_row is not None:
            valid_numbers_by_row[valid_row].append(num)
    
    return valid_numbers_by_row


def try_build_sudoku_grid(numbers: list[str]) -> list[str] | None:
    """
    Try to build a valid Sudoku grid from the given numbers.
    
    Args:
        numbers: List of candidate numbers
        
    Returns:
        Valid grid if found, None otherwise
    """
    valid_numbers_by_row = categorize_numbers_by_row(numbers)
    
    # Early exit if any row has no valid numbers
    if any(not valid_numbers_by_row[i] for i in range(9)):
        return None

    # Initialize tracking for columns and boxes
    column_sets = [set() for _ in range(9)]  # One set for each column
    box_sets = [set() for _ in range(9)]  # One set for each 3x3 box

    def backtrack(grid: list[str], used_numbers: set[str]) -> list[str] | None:
        """
        Backtracking helper to build the Sudoku grid.

        Args:
            grid: Current state of the grid.
            used_numbers: Set of numbers already used in the grid.

        Returns:
            Completed grid if successful, None otherwise.
        """
        if len(grid) == 9:
            return grid  # A full grid is complete and valid

        row_idx = len(grid)  # Current row to fill
        for num in valid_numbers_by_row[row_idx]:
            if num in used_numbers:
                continue  # Skip numbers already used
            
            # Check if the number can be added without violating column and box constraints
            is_valid = True
            for col, digit in enumerate(num):
                # Check column constraints
                if digit in column_sets[col]:
                    is_valid = False
                    break

                # Check box constraints
                box_index = (row_idx // 3) * 3 + (col // 3)
                if digit in box_sets[box_index]:
                    is_valid = False
                    break

            if not is_valid:
                continue

            # Add the number to the grid and update tracking
            grid.append(num)
            used_numbers.add(num)
            for col, digit in enumerate(num):
                column_sets[col].add(digit)
                box_index = (row_idx // 3) * 3 + (col // 3)
                box_sets[box_index].add(digit)

            # Recurse to fill the next row
            result = backtrack(grid, used_numbers)
            if result is not None:
                return result  # Valid grid found

            # Backtrack: Remove the number and revert tracking
            grid.pop()
            used_numbers.remove(num)
            for col, digit in enumerate(num):
                column_sets[col].remove(digit)
                box_index = (row_idx // 3) * 3 + (col // 3)
                box_sets[box_index].remove(digit)

        return None

    return backtrack([], set())


def analyze_divisor(divisor: int, count: int, numbers: list[int], symbols: set[str]) -> bool:
    """
    Analyze a single divisor and try to build a Sudoku grid if possible.
    
    Args:
        divisor: Divisor to analyze.
        count: Number of times this divisor appears.
        numbers: List of all permuted numbers.
        symbols: Set of valid digits.
        
    Returns:
        True if a valid Sudoku grid was found.
    """
    divisible_numbers = find_numbers_with_divisor(numbers, divisor)
    position_digits = check_digit_positions(divisible_numbers, symbols)
    
    all_positions_complete = all(len(digits) == len(symbols) for digits in position_digits)
    
    if all_positions_complete:
        print(f"\nDivisor {divisor} (appears {count} times):")
        print("All digits present in all positions!")
        print("Attempting to build Sudoku grid...")
        
        grid = try_build_sudoku_grid(divisible_numbers)
        if grid is not None:
            print("\nFound valid Sudoku grid!")
            print("\n".join(grid))
            return True
        else:
            print("Could not build valid Sudoku grid with these numbers.")
    
    return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Find a valid Sudoku grid using numbers without a specific digit.'
    )
    parser.add_argument(
        'excluded_digit',
        type=str,
        choices=['1', '3', '4', '6', '7', '8', '9'],
        help='Digit to exclude (cannot be 0, 2, or 5)'
    )
    return parser.parse_args()


def main() -> None:
    """Main function to run the Sudoku grid finder."""
    args = parse_args()
    
    symbols = generate_symbols(args.excluded_digit)
    numbers = generate_permutations(symbols)
    
    divisor_counts = build_divisor_counts(numbers)
    
    print(f"\nAnalyzing positions for divisors with count >= 9:")
    for divisor, count in sorted(divisor_counts.items(), reverse=True):
        if count >= 9:
            if analyze_divisor(divisor, count, numbers, symbols):
                break


if __name__ == "__main__":
    main()