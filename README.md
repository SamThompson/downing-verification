Command line arguments:
=======================
Usage: verification.py [options]

Options:
  -h, --help            show this help message and exit
  -f CSV_FILE           csv file to be read
  -u USER               email address
  -p PASSW              email password
  --smtp=SMTP           smtp server
  --cc=CC               email cc's
  --files=FILES         required files
  --csv_time=CSV_TIME   csv time column index
  --csv_eid=CSV_EID     csv eid column index
  --csv_email=CSV_EMAIL
                        csv email column index
  --csv_url=CSV_URL     csv url column index
  --csv_sha=CSV_SHA     csv sha column index



An example call
================

Executed in the directory where you want to download all of the projects

```
$ /path/to/verification.py -f <input_csv> -u <your email address> -p <your email pwd> \
    --smtp <smtp server> --cc <list of people to cc> --files <list of files to check> \
    --csv_time <some integer> --csv_eid <some integer> --csv_email <some integer> \
    --csv_url <some integer> --csv_sha <some integer>
```

