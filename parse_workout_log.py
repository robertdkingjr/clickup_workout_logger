import re
import pandas as pd
import plotly.express as px

# mm/dd/yy
re_date = re.compile(r"(\d+/\d+/*\d*).*")

# exercise reps x weight
re_exercise = re.compile(r"([ \-]*)([a-zA-Z\s/()]+)[\d]+x[*]?[a-zA-Z\s]*\d+")

# reps x weight
re_reps = re.compile(r"([\d]+)x([*]?)[\sa-zA-Z]*([\d.]+)")


def print_red(text):
    print('\033[31m', text, '\033[0m')


def print_green(text):
    print('\033[32m', text, '\033[0m')


def print_orange(text):
    print('\033[33m', text, '\033[0m')


def parse_log(file_path, output_csv_path):

    workout_data = []
    with open(file_path) as workout_log:

        active_date = None
        for i, line in enumerate(workout_log.readlines()):

            # Ignore empty lines, reset date
            if line.strip() == "":
                active_date = None
                continue

            # # debugging
            # if i > 10:
            #     exit()

            line = line.replace("BW", "160")
            line = line.replace("WU", "7")

            # Check for dates
            date_match = re_date.match(line)
            exercise_match = re_exercise.match(line)

            if date_match:
                active_date = date_match.group(1)
                if len(active_date) < 6:  # m/d/yy vs mm/dd
                    active_date = f"{active_date}/22"

                print_green(f'active_date = {active_date}')

                # Move to next line
                continue

            # Check for exercise set
            elif exercise_match:

                # Extract exercise from regex match
                exercise = exercise_match.group(2).strip(" ")

                # Replace " with previous set - e.g. curl 7x30, ", 35, ", "
                # Fill in reps for repeated sets - e.g. 7x50, 50, 60, 70
                tokens = line.split(" ")
                new_line = ""
                print(line)
                last_good_token = None
                for token in tokens:
                    print(token)
                    reps_match = re_reps.match(token)
                    if reps_match:
                        reps = reps_match.group(1)
                        new_line += f"{token} "
                        last_good_token = token
                    elif token.strip().strip(",").replace(".", "").isnumeric():
                        new_token = f"{reps}x{token},"
                        new_line += new_token
                        last_good_token = new_token
                        print_orange(f"replaced token, newline = {new_line}")
                    elif '"' in token:
                        new_line += last_good_token  # use previous token
                    else:
                        print(f"ignoring {token}")
                line = new_line
                print_orange(f"final newline = {line}")

                # Loop over reps identified in line
                for reps, failed, weight in re_reps.findall(line):
                    failed = (failed == "*")
                    print(f'{exercise} set = {reps} x {weight} (failed = {failed})')

                    # Ignore warmup ("wu") sets
                    if str(reps).lower().strip() in ("wu", "bw"):
                        continue

                    workout_data.append(dict(
                        date=active_date,
                        exercise=exercise,
                        reps=reps,
                        weight=weight
                    ))

                pass
            else:
                stripped_line = line.strip('\n')
                print_red(f"Ignoring line: {stripped_line}")
                continue

            # todo Check for subset

            # Check for comments?
            pass

        df = pd.DataFrame(workout_data)
        df.to_csv(output_csv_path)


def plot_workouts(csv_data_path):

    df = pd.read_csv(csv_data_path)
    df['date'] = pd.to_datetime(df['date'])

    fig = px.scatter(df, x="date", y="weight", color="exercise", size="reps")
    # fig.show()
    fig.write_html("./workout_weight_over_time.html", auto_open=True)


if __name__ == '__main__':
    input_file = "workout_log.txt"
    csv_file = "workout_data.csv"

    parse_log(file_path=input_file, output_csv_path=csv_file)
    plot_workouts(csv_data_path=csv_file)
