from apollo import Apollo

RED_ANSI = "\033[31m"
GREEN_ANSI = "\033[32m"
RESET_ANSI = "\033[0m"
BLUE_ANSI = "\033[34m"

def run():
  print(f"{BLUE_ANSI}Type h for help or q to quit.{RESET_ANSI}")

  day_to_extract_is_valid = False
  while day_to_extract_is_valid == False:
    day_to_extract = input(f"\nWhich day's songs to extract (0-7): {GREEN_ANSI}")
    print(f"{RESET_ANSI}", end="")

    if day_to_extract == "q":
      return 0

    if day_to_extract == "":
      day_to_extract = 1

    if day_to_extract == "h" or day_to_extract == "H":
      print(f"\n{BLUE_ANSI}To select which day's songs from Radio Koper to extract, type a number between 0 and 7.")
      print("Meaning of the numbers:")
      print("  - 0 = today")
      print("  - 1 = 1 day ago")
      print("  - 2 = 2 days ago")
      print("  - ...")
      print("  - 7 = 7 days ago")
      print(f"If you do not select enything, the default selection is 1, so yesterday.{RESET_ANSI}")
    else:
      day_to_extract_is_valid = True

  try:
    day_to_extract = int(day_to_extract)
  except ValueError:
    print(f"{RED_ANSI}Invalid entry. Select a number between 0 and 7.{RESET_ANSI}")
    return 1


  if day_to_extract < 0 or day_to_extract > 7:
    print(f"{RED_ANSI}Invalid entry. Select a number between 0 and 7.{RESET_ANSI}")
    return 1

  Apollo().run(day_to_extract)

if __name__ == "__main__":
  run()