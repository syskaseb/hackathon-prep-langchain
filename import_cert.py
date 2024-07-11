import os
import certifi
import subprocess


def download_certificate_with_curl(url, filename):
    try:
        subprocess.run(["curl", "-o", filename, url], check=True)
        print(f"Downloaded certificate to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error downloading certificate: {e}")
        raise


def append_certificate_to_cacert(ca_cert_path, cacert_path):
    with open(ca_cert_path, 'r') as ca_file:
        ca_cert_data = ca_file.read()

    with open(cacert_path, 'r') as cacert_file:
        cacert_data = cacert_file.read()

    if ca_cert_data not in cacert_data:
        with open(cacert_path, 'a') as cacert_file:
            cacert_file.write('\n' + ca_cert_data)
        print("Certificate appended to cacert.pem")
    else:
        print("Certificate already present in cacert.pem")


def main():
    ca_cert_url = "https://developers.cloudflare.com/cloudflare-one/static/Cloudflare_CA.pem"
    ca_cert_filename = "Cloudflare_CA.pem"

    # Download the Cloudflare CA certificate using curl
    download_certificate_with_curl(ca_cert_url, ca_cert_filename)

    # Get the path to the cacert.pem file in the current virtual environment
    cacert_path = certifi.where()

    # Append the downloaded certificate to the cacert.pem file if not present
    append_certificate_to_cacert(ca_cert_filename, cacert_path)

    # Clean up the downloaded certificate file
    os.remove(ca_cert_filename)


if __name__ == "__main__":
    main()
