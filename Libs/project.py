import json
import os
import logging

from . import project_structure_path

logger = logging.getLogger(__name__)

def create_project_structure(base_path, structure):
    for name, contents in structure.items():
        path = os.path.join(base_path, name)
        os.makedirs(path, exist_ok=True)
        logger.debug("Created directory: %s", path)

        if isinstance(contents, dict):  # A subdirectory
            create_project_structure(path, contents)
        else:
            continue  # A file, do nothing


def CreateProject(project_dir, batch_num=1):
    """
    Create a project structure at base_path from structure.
    """
    logger.info(f"Creating project structure at {project_dir}, batch {batch_num}")

    batch_dir = os.path.join(project_dir, f"Batch {batch_num}")

    with open(project_structure_path, 'r') as f:
        project_structure = json.load(f)

    create_project_structure(batch_dir, project_structure)

    logger.info("Project structure created")

    

