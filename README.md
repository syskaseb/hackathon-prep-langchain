PoC setup steps:

# run postgres container
docker run -p 5432:5432 --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres

# create mock data with psql

CREATE DATABASE jobboard;
\c jobboard
CREATE TABLE job_data (
    job_id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    applications INT,
    location VARCHAR(255),
    posted_date DATE
);

INSERT INTO job_data (title, applications, location, posted_date) VALUES
('Software Engineer', 120, 'New York', '2023-07-01'),
('Data Analyst', 80, 'San Francisco', '2023-06-24'),
('Product Manager', 200, 'Remote', '2023-07-03');

# create venv
python -m venv new-env
source new-env/bin/activate  # On Windows use `new-env\Scripts\activate`

# install dependencies
