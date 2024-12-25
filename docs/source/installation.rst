Installation
To run the code on your local machine, install JupyterLab by running:
pip install jupyterlab
Clone this repository:
git clone (https://github.com/ronikianji/WATcycle.git)
Creating virtual environment
pip install virtualenv
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
pip install ipykernel
python -m ipykernel install --user --name=myenv --display-name "WATcycle"