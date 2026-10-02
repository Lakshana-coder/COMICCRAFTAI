from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    story_prompt: str = Field(
        ...,
        min_length=5,
        max_length=2000,
    )

    character_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    setting: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    tone: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    art_style: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )


class ImageTestRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=1000,
    )