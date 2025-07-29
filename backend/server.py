from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class VideoGenerationRequest(BaseModel):
    prompt: str
    duration: int = Field(default=30, ge=15, le=60)  # 15-60 seconds for TikTok

class GeneratedScript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    duration: int
    script_text: str
    scenes: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GeneratedImage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    image_base64: str
    scene_description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VideoProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_prompt: str
    duration: int
    script_id: str
    image_ids: List[str]
    status: str = "generating"  # generating, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Initialize OpenAI services
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Routes
@api_router.get("/")
async def root():
    return {"message": "TikTok Video Generator API"}

@api_router.post("/generate-script", response_model=GeneratedScript)
async def generate_script(request: VideoGenerationRequest):
    try:
        # Initialize LLM Chat with GPT-4.1
        chat = LlmChat(
            api_key=OPENAI_API_KEY,
            session_id=f"script-gen-{uuid.uuid4()}",
            system_message="""Tu es un expert en création de contenu TikTok. Tu crées des scripts engageants et viraux pour des vidéos courtes.
            
            INSTRUCTIONS:
            1. Crée un script structuré avec des scènes distinctes
            2. Chaque scène doit être visuelle et impactante  
            3. Le ton doit être dynamique et captivant
            4. Adapte la durée selon le nombre de secondes demandées
            5. Divise le script en 3-5 scènes maximum
            6. Chaque scène doit pouvoir être illustrée par une image
            
            FORMAT DE RÉPONSE:
            Script: [Le script complet]
            
            Scènes:
            1. [Description de la scène 1]
            2. [Description de la scène 2]
            etc."""
        ).with_model("openai", "gpt-4.1")

        user_message = UserMessage(
            text=f"Crée un script TikTok de {request.duration} secondes pour le sujet suivant: {request.prompt}"
        )

        response = await chat.send_message(user_message)
        
        # Parse response to extract script and scenes
        response_text = str(response)
        script_text = ""
        scenes = []
        
        if "Script:" in response_text:
            parts = response_text.split("Scènes:")
            script_text = parts[0].replace("Script:", "").strip()
            
            if len(parts) > 1:
                scenes_text = parts[1].strip()
                # Extract numbered scenes
                scene_lines = [line.strip() for line in scenes_text.split('\n') if line.strip()]
                for line in scene_lines:
                    if any(line.startswith(f"{i}.") for i in range(1, 10)):
                        scene_desc = line.split('.', 1)[1].strip() if '.' in line else line
                        scenes.append(scene_desc)
        else:
            script_text = response_text
            # Fallback: split into scenes based on script content
            sentences = script_text.split('.')
            for i in range(0, len(sentences), 2):
                if i < len(sentences):
                    scene = '. '.join(sentences[i:i+2]).strip()
                    if scene:
                        scenes.append(scene)

        # Save to database
        script_obj = GeneratedScript(
            prompt=request.prompt,
            duration=request.duration,
            script_text=script_text,
            scenes=scenes
        )
        
        await db.scripts.insert_one(script_obj.dict())
        return script_obj

    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating script: {str(e)}")

@api_router.post("/generate-images")
async def generate_images(script_id: str):
    try:
        # Get script from database
        script_data = await db.scripts.find_one({"id": script_id})
        if not script_data:
            raise HTTPException(status_code=404, detail="Script not found")

        script_obj = GeneratedScript(**script_data)
        
        # Initialize OpenAI Image Generation  
        image_gen = OpenAIImageGeneration(api_key=OPENAI_API_KEY)
        
        generated_images = []
        
        for i, scene in enumerate(script_obj.scenes):
            # Create charcoal-style prompt
            charcoal_prompt = f"""Style charbon artistique dramatique: {scene}. 
            Palette noir, gris, blanc exclusivement. Effet granuleux, ombres fortes, textures riches.
            Technique fusain, charbon compressé, estompage. Atmosphère dramatique, émotion brute, esthétisme expressif.
            Composition cinématographique, éclairage contrasté, détails texturés."""
            
            try:
                # Try gpt-image-1 first, fallback to dall-e-3 if 403 error
                images = None
                try:
                    images = await image_gen.generate_images(
                        prompt=charcoal_prompt,
                        model="gpt-image-1",
                        number_of_images=1
                    )
                except Exception as gpt_error:
                    if "403" in str(gpt_error) or "verification" in str(gpt_error).lower():
                        logger.info(f"gpt-image-1 requires verification, falling back to dall-e-3")
                        images = await image_gen.generate_images(
                            prompt=charcoal_prompt,
                            model="dall-e-3",
                            number_of_images=1
                        )
                    else:
                        raise gpt_error
                
                if images and len(images) > 0:
                    # Convert to base64
                    image_base64 = base64.b64encode(images[0]).decode('utf-8')
                    
                    # Create image object
                    image_obj = GeneratedImage(
                        prompt=charcoal_prompt,
                        image_base64=image_base64,
                        scene_description=scene
                    )
                    
                    await db.images.insert_one(image_obj.dict())
                    generated_images.append(image_obj)
                    
            except Exception as img_error:
                logger.error(f"Error generating image for scene {i}: {str(img_error)}")
                # Continue with other scenes even if one fails
                continue
        
        return {
            "script_id": script_id,
            "images": generated_images,
            "total_generated": len(generated_images)
        }

    except Exception as e:
        logger.error(f"Error generating images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating images: {str(e)}")

@api_router.post("/create-video-project", response_model=VideoProject)
async def create_video_project(request: VideoGenerationRequest):
    try:
        # Generate script first
        script_response = await generate_script(request)
        
        # Generate images
        images_response = await generate_images(script_response.id)
        
        # Create video project
        project_obj = VideoProject(
            original_prompt=request.prompt,
            duration=request.duration,
            script_id=script_response.id,
            image_ids=[img.id for img in images_response["images"]],
            status="completed"
        )
        
        await db.projects.insert_one(project_obj.dict())
        return project_obj

    except Exception as e:
        logger.error(f"Error creating video project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating video project: {str(e)}")

@api_router.get("/project/{project_id}")
async def get_project(project_id: str):
    try:
        # Get project
        project_data = await db.projects.find_one({"id": project_id})
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get script
        script_data = await db.scripts.find_one({"id": project_data["script_id"]})
        
        # Get images
        images_data = await db.images.find({"id": {"$in": project_data["image_ids"]}}).to_list(1000)
        
        return {
            "project": project_data,
            "script": script_data,
            "images": images_data
        }

    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting project: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()