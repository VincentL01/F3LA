import json
import os
import logging

from . import project_structure_path
from Libs.misc import index_to_char

logger = logging.getLogger(__name__)

def make_project_structure(base_path, structure):
    for name, contents in structure.items():
        path = os.path.join(base_path, name)
        os.makedirs(path, exist_ok=True)
        logger.debug("Created directory: %s", path)

        if isinstance(contents, dict):  # A subdirectory
            make_project_structure(path, contents)
        else:
            continue  # A file, do nothing


def create_structure(treatment_info):

    output_structure = {}
    output_structure["static"] = {}

    for i, info in enumerate(treatment_info):
        contents = info.split()
        treatment_char = index_to_char(i)
        if len(contents) <= 2:
            treatment_dir_name = f"{treatment_char} - {contents[0]}"
        elif len(contents) == 3:
            treatment_dir_name = f"{treatment_char} - {contents[0]} {contents[1]}{contents[2]}"
        else:
            unit = contents[-1]
            dose = contents[-2]
            substance = " ".join(contents[:-2])
            treatment_dir_name = f"{treatment_char} - {substance} {dose}{unit}"
            logger.warning(f"Substance has space in name, treatment_dir = {treatment_dir_name}")
        
        output_structure[treatment_dir_name] = {"Side View": 0,
                                                "Top View" : 0}
        
        output_structure["static"][treatment_char] = 0

    return output_structure


def CreateProject(project_dir, treatment_info, batch_num=1):
    """
    Create a project structure at base_path from structure.
    """
    logger.info(f"Creating project structure at {project_dir}, batch {batch_num}")

    batch_dir = os.path.join(project_dir, f"Batch {batch_num}")

    project_structure = create_structure(treatment_info)

    make_project_structure(batch_dir, project_structure)

    logger.info("Project structure created")

    

