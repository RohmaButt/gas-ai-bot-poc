def format_results(cursor, results):
    """Formats database results into a user-friendly string."""
    if not results:
        return "No results found."

    headers = [description[0] for description in cursor.description]
    formatted_results = [headers]

    for row in results:
        formatted_results.append([str(item) for item in row])

    # Calculate column widths
    column_widths = [max(len(item) for item in col) for col in zip(*formatted_results)]

    # Create the formatted table
    formatted_table = ""
    for i, row in enumerate(formatted_results):
        formatted_table += " | ".join(item.ljust(width) for item, width in zip(row, column_widths)) + "\n"
        if i == 0:
            formatted_table += "-" * (sum(column_widths) + 3 * (len(column_widths) - 1)) + "\n"

    return formatted_table