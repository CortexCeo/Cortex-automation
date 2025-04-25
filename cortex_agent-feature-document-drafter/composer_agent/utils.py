from composer_agent.state import Artifact, ComposerState


def get_artifact_content(artifact: Artifact) -> dict:
    """
    Retrieves the content of an artifact based on its current index.

    Args:
        artifact: The Artifact object.

    Returns:
        The ArtifactCodeV3 or ArtifactMarkdownV3 object corresponding to the current index,
        or the last content if the current index is not found.

    Raises:
        ValueError: If the artifact is None.
    """
    if not artifact:
        raise ValueError("No artifact found.")

    current_content = next((content for content in artifact.contents if content["index"] == artifact.current_index), None)

    if not current_content:
        return artifact.contents[-1] if artifact.contents else None # added None check in case contents is empty

    return current_content

def validate_state(state: ComposerState):
    current_artifact_content = get_artifact_content(state.artifact) if state.artifact else None
    if not current_artifact_content:
        raise Exception("No artifact found")
    
    # Find the last human message by iterating in reverse.
    recent_human_message = next(
        (msg for msg in reversed(state.messages) if msg.type == "human"),
        None
    )
    if not recent_human_message:
        raise Exception("No recent human message found")
    
    return {"current_artifact_content": current_artifact_content, "recent_human_message": recent_human_message}
