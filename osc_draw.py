def integer_to_twos_complement(integer):
    # Convert the integer to a binary string and remove the '0b' prefix
    binary_str = format(integer, "b")

    # Pad the binary string with leading zeros to ensure it's at least 16 characters long
    padded_binary_str = binary_str.zfill(16)

    # Split the padded binary string into two 8-character substrings
    first_half = padded_binary_str[:8]
    second_half = padded_binary_str[8:]

    # Define a helper function to convert an 8-bit binary to two's complement decimal
    def binary_to_twos_complement(bin_str):
        # Consider the binary to be negative if it starts with '1'
        if bin_str[0] == "1":
            # Convert into a decimal integer by inverting bits and adding 1 (two's complement)
            return -((int(bin_str, 2) ^ 0xFF) + 1)
        else:
            # Simply convert to a decimal integer
            return int(bin_str, 2)

    # Convert both halves to their two's complement decimal form
    # The two values are switched in the S-1 e.g., (button2, button1), (button 4, button3)
    first_decimal = binary_to_twos_complement(second_half)
    second_decimal = binary_to_twos_complement(first_half)

    return first_decimal, second_decimal


# The two values are switched in the S-1 e.g., (button2, button1), (button 4, button3)
def twos_complement_to_integer(second_decimal, first_decimal):
    # Define a helper function to convert a signed decimal to an 8-bit binary string
    def twos_complement_to_binary_string(value):
        if value < 0:
            # Calculate the two's complement 8-bit representation of the negative number
            value = (abs(value) ^ 0xFF) + 1
        # Convert to binary and extract the last 8 bits (8 characters)
        return format(value & 0xFF, "08b")

    # Convert both integers to 8-bit binary strings
    first_half = twos_complement_to_binary_string(first_decimal)
    second_half = twos_complement_to_binary_string(second_decimal)

    # Concatenate the two binary strings to form a 16-bit binary string
    combined_binary = first_half + second_half

    # Convert the 16-bit binary string to an integer
    result_integer = int(combined_binary, 2)

    return result_integer


for x in (44444, 51387, 58069, 64751, 5641, 12323, 19005, 25687):
    print(integer_to_twos_complement(x))
