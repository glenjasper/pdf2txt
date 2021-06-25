pdf2txt
======================
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](./LICENSE)

This script converts .pdf files to .txt files.

## Table of content

- [Pre-requisites](#pre-requisites)
    - [Python libraries](#python-libraries)
- [Installation](#installation)
    - [Clone](#clone)
    - [Download](#download)
- [Built With](#built-with)
- [How To Use](#how-to-use)
- [Author](#author)
- [Organization](#organization)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Pre-requisites

### Python libraries

```sh
  $ sudo apt install -y python3-pip
  $ sudo pip3 install --upgrade pip
```

```sh
  $ sudo pip3 install argparse
  $ sudo pip3 install xlsxwriter
  $ sudo pip3 install pandas
```

## Installation

### Clone

To clone and run this application, you'll need [Git](https://git-scm.com) installed on your computer. From your command line:

```bash
  # Clone this repository
  $ git clone https://github.com/glenjasper/pdf2txt.git

  # Go into the repository
  $ cd pdf2txt

  # Run the app
  $ python3 pdf2txt.py --help
```

### Download

You can [download](https://github.com/glenjasper/pdf2txt/archive/master.zip) the latest installable version of _pdf2txt_.

## Built With

* [XpdfReader](http://www.xpdfreader.com): Xpdf is a free PDF viewer and toolkit, including a text extractor, image converter, HTML converter, and more. Most of the tools are available as open source.

## How To Use

```sh  
  $ python3 pdf2txt.py --help
  usage: pdf2txt.py [-h] -f FOLDER_PDF [-o OUTPUT] [--version]

  This script converts .pdf files to .txt files.

  optional arguments:
    -h, --help            show this help message and exit
    -f FOLDER_PDF, --folder_pdf FOLDER_PDF
                          Folder that contains all .pdf files
    -o OUTPUT, --output OUTPUT
                          Output folder
    --version             show program's version number and exit

  Thank you!
```

## Author

* [Glen Jasper](https://github.com/glenjasper)

## Organization
* [Molecular and Computational Biology of Fungi Laboratory](http://lbmcf.pythonanywhere.com) (LBMCF, ICB - **UFMG**, Belo Horizonte, Brazil).

## License

This project is licensed under the GNU General Public License v3.0 License - see the [LICENSE](./LICENSE) file for details.
