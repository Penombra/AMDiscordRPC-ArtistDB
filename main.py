import subprocess
import duckdb
import shutil
import requests
from requests.compat import quote
from tqdm import tqdm

dumpUrl = "https://data.metabrainz.org/pub/musicbrainz/data/fullexport/"
query = r"""
    CREATE TABLE sqlite_db.artists AS 
    SELECT column02 AS artist 
    FROM read_csv_auto(
        'mbdump/artist',
        header=False,
        delim='\t',
        quote='',
        nullstr='\N',
        all_varchar=True
    ) 
    WHERE column02 LIKE '% & %' OR column02 LIKE '%, %';
"""

def download_database_dump():
    with requests.get(dumpUrl + "LATEST") as r:
        r.raise_for_status()
        with requests.get(dumpUrl + r.text.split("\n")[0] + "/mbdump.tar.bz2", stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total = total_size, unit ='B', unit_scale=True, desc="Downloading")
            chunk_size = 1024 * 1024
            with open("mbdump.tar.bz2", 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))
            progress_bar.close()
        print("Download finished!")

def create_filtered_sqlite():
    con = duckdb.connect()
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute("ATTACH 'artists.db' AS sqlite_db (TYPE sqlite);")
    con.execute(query)

# I will add comparasion method later to compare the results with the last results.

download_database_dump()
subprocess.run(["tar", "-I", "lbzip2", "-xvf", "mbdump.tar.bz2", "mbdump/artist"])
create_filtered_sqlite()
shutil.rmtree("mbdump")