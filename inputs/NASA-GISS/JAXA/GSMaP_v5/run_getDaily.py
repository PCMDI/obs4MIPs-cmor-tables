from getDaily import run_month

if __name__ == "__main__":

    year = "2023"

    for mon in range(1, 2):

        run_month(
            year,
            f"{mon:02d}",
            nproc=16
        )
