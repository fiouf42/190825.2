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
from openai import AsyncOpenAI
from elevenlabs.client import AsyncElevenLabs
import ffmpeg
import tempfile
import io
import asyncio
import httpx
from pathlib import Path

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
    voice_id: str = Field(default="pNInz6obpgDQGcFmaJgB")  # Default voice ID

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

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI and ElevenLabs clients
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

# Initialize clients with error handling
try:
    # Create custom httpx client to avoid proxies parameter issue
    import httpx
    custom_client = httpx.AsyncClient(timeout=60.0)
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, http_client=custom_client)
    logger.info("OpenAI client initialized successfully with custom httpx client")
except Exception as e:
    logger.error(f"Error initializing OpenAI client with custom client: {e}")
    try:
        # Fallback: try with minimal parameters
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized with minimal parameters")
    except Exception as e2:
        logger.error(f"Failed to initialize OpenAI client: {e2}")
        raise e2

# Voice models - we'll try to find Nicolas voice or use a good French male voice
FRENCH_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - male English (we'll update this after testing)

class GeneratedAudio(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    script_id: str
    audio_base64: str
    voice_id: str = FRENCH_VOICE_ID
    duration: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VideoAssemblyResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    video_base64: str
    duration: float
    resolution: str = "1080x1920"  # TikTok format
    created_at: datetime = Field(default_factory=datetime.utcnow)

def create_subtitle_file(script_text: str, duration: float) -> str:
    """Create SRT subtitle file from script with TikTok-style timing"""
    # Split text into words for better TikTok-style appearance
    words = script_text.replace('\n', ' ').split()
    if not words:
        return ""
    
    srt_content = ""
    
    # For TikTok style, we want shorter segments with more dynamic timing
    # Group words into smaller chunks (3-5 words per subtitle)
    words_per_subtitle = 4
    word_groups = []
    
    for i in range(0, len(words), words_per_subtitle):
        group = ' '.join(words[i:i + words_per_subtitle])
        word_groups.append(group)
    
    if not word_groups:
        return ""
    
    # Calculate timing - TikTok style with quick transitions
    time_per_group = duration / len(word_groups)
    overlap = 0.1  # Small overlap for smoother transitions
    
    for i, group in enumerate(word_groups):
        start_time = max(0, i * time_per_group - overlap)
        end_time = min(duration, (i + 1) * time_per_group + overlap)
        
        # Convert to SRT time format
        start_h = int(start_time // 3600)
        start_m = int((start_time % 3600) // 60)
        start_s = int(start_time % 60)
        start_ms = int((start_time % 1) * 1000)
        
        end_h = int(end_time // 3600)
        end_m = int((end_time % 3600) // 60)
        end_s = int(end_time % 60)
        end_ms = int((end_time % 1) * 1000)
        
        srt_content += f"{i + 1}\n"
        srt_content += f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> {end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n"
        srt_content += f"{group.upper()}\n\n"  # Uppercase for TikTok style
    
    return srt_content

async def assemble_video(project_id: str, images: List[dict], audio_base64: str, script_text: str, duration: float) -> str:
    """Assemble final video using FFmpeg with simplified but effective transitions"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save audio file
            audio_path = temp_path / "audio.wav"
            audio_data = base64.b64decode(audio_base64)
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            
            # Save images
            image_paths = []
            for i, image in enumerate(images):
                img_path = temp_path / f"image_{i}.png"
                # Handle both dict and Pydantic object formats
                if hasattr(image, 'image_base64'):
                    img_data = base64.b64decode(image.image_base64)
                else:
                    img_data = base64.b64decode(image['image_base64'])
                with open(img_path, "wb") as f:
                    f.write(img_data)
                image_paths.append(img_path)
            
            # Create subtitle file
            subtitle_path = temp_path / "subtitles.srt"
            srt_content = create_subtitle_file(script_text, duration)
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            # Calculate duration per image
            image_duration = duration / len(images) if images else duration
            output_path = temp_path / "final_video.mp4"
            
            if len(image_paths) == 1:
                # Single image video with improved TikTok-style subtitles
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1', '-t', str(duration), '-i', str(image_paths[0]),
                    '-i', str(audio_path),
                    '-filter_complex', 
                    f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',subtitles='{subtitle_path}':force_style='Fontname=Arial Black,Fontsize=36,Bold=1,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,BackColour=&H000000&,Outline=3,Shadow=2,Alignment=2,MarginV=120'[final]",
                    '-map', '[final]',
                    '-map', '1:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-shortest', '-r', '25',
                    str(output_path)
                ]
            else:
                # Multiple images with transitions
                # First, create a simple concatenation with crossfade
                inputs = []
                filter_parts = []
                
                # Add all image inputs
                for i, img_path in enumerate(image_paths):
                    inputs.extend(['-loop', '1', '-t', str(image_duration + 1), '-i', str(img_path)])
                    # Scale each input
                    filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v{i}]")
                
                # Add audio input (will be the last input)
                inputs.extend(['-i', str(audio_path)])
                audio_index = len(image_paths)
                
                # Create crossfade transitions
                if len(image_paths) == 2:
                    filter_parts.append(f"[v0][v1]xfade=transition=fade:duration=0.5:offset={image_duration}[xfaded]")
                    final_filter = f"[xfaded]zoompan=z='if(lte(zoom,1.0),1.2,max(1.001,zoom-0.0010))':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',subtitles='{subtitle_path}':force_style='Fontsize=24,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,BorderStyle=3'[final]"
                else:
                    # For 3+ images, chain crossfades
                    filter_parts.append(f"[v0][v1]xfade=transition=fade:duration=0.5:offset={image_duration}[xf0]")
                    for i in range(2, len(image_paths)):
                        prev_label = f"xf{i-2}"
                        filter_parts.append(f"[{prev_label}][v{i}]xfade=transition=fade:duration=0.5:offset={image_duration*i}[xf{i-1}]")
                    
                    last_xf_label = f"xf{len(image_paths)-2}"
                    final_filter = f"[{last_xf_label}]zoompan=z='if(lte(zoom,1.0),1.2,max(1.001,zoom-0.0010))':d=25:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',subtitles='{subtitle_path}':force_style='Fontsize=24,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,BorderStyle=3'[final]"
                
                filter_parts.append(final_filter)
                filter_complex = ";".join(filter_parts)
                
                cmd = [
                    'ffmpeg', '-y'
                ] + inputs + [
                    '-filter_complex', filter_complex,
                    '-map', '[final]',
                    '-map', f'{audio_index}:a',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-shortest', '-r', '25',
                    str(output_path)
                ]
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                logger.error(f"FFmpeg failed: {error_msg}")
                raise Exception(f"Video assembly failed: {error_msg}")
            
            # Read the final video and convert to base64
            with open(output_path, 'rb') as f:
                video_data = f.read()
            
            video_base64 = base64.b64encode(video_data).decode('utf-8')
            logger.info(f"Video assembled successfully: {len(video_data)} bytes, {len(video_base64)} base64 chars")
            
            return video_base64
            
    except Exception as e:
        logger.error(f"Error assembling video: {str(e)}")
        raise Exception(f"Video assembly failed: {str(e)}")

async def get_elevenlabs_client():
    """Get ElevenLabs client instance"""
    import httpx
    # Create custom httpx client with timeout
    httpx_client = httpx.AsyncClient(timeout=30.0)
    return AsyncElevenLabs(
        api_key=ELEVENLABS_API_KEY,
        httpx_client=httpx_client
    )

# Routes
@api_router.get("/")
async def root():
    return {"message": "TikTok Video Generator API"}

@api_router.post("/generate-script", response_model=GeneratedScript)
async def generate_script(request: VideoGenerationRequest):
    try:
        # Use OpenAI ChatCompletion API for script generation
        response = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un expert en création de contenu TikTok. Tu crées des scripts engageants et viraux pour des vidéos courtes.
                    
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
                },
                {
                    "role": "user",
                    "content": f"Crée un script TikTok de {request.duration} secondes pour le sujet suivant: {request.prompt}"
                }
            ]
        )
        
        # Parse response to extract script and scenes
        response_text = response.choices[0].message.content
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

@api_router.post("/generate-voice")
async def generate_voice(script_id: str, voice_id: str = "pNInz6obpgDQGcFmaJgB"):
    """Generate voice narration from script using ElevenLabs"""
    try:
        # Get script from database
        script_data = await db.scripts.find_one({"id": script_id})
        if not script_data:
            raise HTTPException(status_code=404, detail="Script not found")

        script_obj = GeneratedScript(**script_data)
        
        # Initialize ElevenLabs client
        client = await get_elevenlabs_client()
        
        # Use the provided voice_id directly
        selected_voice_id = voice_id
        logger.info(f"Using voice ID: {selected_voice_id}")
        
        # Validate voice exists by checking available voices
        try:
            voices = await client.voices.get_all()
            voice_names = {voice.voice_id: voice.name for voice in voices.voices}
            if selected_voice_id in voice_names:
                logger.info(f"Voice validated: {voice_names[selected_voice_id]} ({selected_voice_id})")
            else:
                logger.warning(f"Voice ID {selected_voice_id} not found, using default")
                selected_voice_id = "pNInz6obpgDQGcFmaJgB"  # Default fallback
        except Exception as voice_error:
            logger.warning(f"Could not validate voice: {voice_error}, proceeding with provided voice_id")
        
        # Generate audio from script text
        try:
            # Use the full script text for narration
            text_to_speak = script_obj.script_text
            
            # Generate audio
            audio_generator = client.text_to_speech.convert(
                text=text_to_speak,
                voice_id=selected_voice_id,
                model_id="eleven_multilingual_v2",  # Best for French
                voice_settings={
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.3,
                    "use_speaker_boost": True
                }
            )
            
            # Collect audio chunks
            audio_chunks = []
            async for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            # Combine chunks
            audio_data = b''.join(audio_chunks)
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Calculate duration (approximation)
            duration = len(text_to_speak) * 0.1  # Rough estimate
            
            # Create audio object
            audio_obj = GeneratedAudio(
                script_id=script_id,
                audio_base64=audio_base64,
                voice_id=selected_voice_id,
                duration=duration
            )
            
            # Save to database
            await db.audio.insert_one(audio_obj.dict())
            
            return {
                "audio_id": audio_obj.id,
                "script_id": script_id,
                "voice_id": selected_voice_id,
                "duration": duration,
                "audio_base64": audio_base64,
                "message": "ElevenLabs audio generated successfully"
            }
            
        except Exception as tts_error:
            logger.error(f"Error generating TTS: {str(tts_error)}")
            raise HTTPException(status_code=500, detail=f"Error generating voice: {str(tts_error)}")

    except Exception as e:
        logger.error(f"Error in generate_voice: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating voice: {str(e)}")

@api_router.get("/voices/available")
async def get_available_voices():
    """Get all available voices from ElevenLabs"""
    try:
        client = await get_elevenlabs_client()
        voices = await client.voices.get_all()
        
        voice_list = []
        for voice in voices.voices:
            voice_list.append({
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": getattr(voice, 'description', ''),
                "preview_url": getattr(voice, 'preview_url', '')
            })
        
        return {"voices": voice_list}
        
    except Exception as e:
        logger.error(f"Error fetching voices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching voices: {str(e)}")

@api_router.post("/generate-images")
async def generate_images(script_id: str):
    try:
        # Get script from database
        script_data = await db.scripts.find_one({"id": script_id})
        if not script_data:
            raise HTTPException(status_code=404, detail="Script not found")

        script_obj = GeneratedScript(**script_data)
        
        generated_images = []
        
        for i, scene in enumerate(script_obj.scenes):
            # Create charcoal-style prompt
            charcoal_prompt = f"""Style charbon artistique dramatique: {scene}. 
            Palette noir, gris, blanc exclusivement. Effet granuleux, ombres fortes, textures riches.
            Technique fusain, charbon compressé, estompage. Atmosphère dramatique, émotion brute, esthétisme expressif.
            Composition cinématographique, éclairage contrasté, détails texturés."""
            
            try:
                # Use OpenAI Images API
                response = await openai_client.images.generate(
                    model="dall-e-3",
                    prompt=charcoal_prompt,
                    size="1024x1024",
                    quality="standard",
                    response_format="b64_json",
                    n=1
                )
                
                # Extract base64 image data
                image_base64 = response.data[0].b64_json
                
                # Validate base64 data
                if not image_base64 or len(image_base64) < 100:
                    logger.error(f"Invalid or empty base64 data for image {i}")
                    continue
                
                logger.info(f"Successfully generated image {i} with {len(image_base64)} chars of base64 data")
                
                # Create image object
                image_obj = GeneratedImage(
                    prompt=charcoal_prompt,
                    image_base64=image_base64,
                    scene_description=scene
                )
                
                await db.images.insert_one(image_obj.dict())
                generated_images.append(image_obj)
                logger.info(f"Image {i} saved to database with ID: {image_obj.id}")
                    
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

@api_router.post("/assemble-video")
async def assemble_final_video(project_id: str):
    """Assemble final video with images, voice, and subtitles"""
    try:
        # Get project data
        project_data = await db.projects.find_one({"id": project_id})
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get script
        script_data = await db.scripts.find_one({"id": project_data["script_id"]})
        if not script_data:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # Get images
        images_data = await db.images.find({"id": {"$in": project_data["image_ids"]}}).to_list(1000)
        if not images_data:
            raise HTTPException(status_code=404, detail="Images not found")
        
        # Get audio
        audio_data = await db.audio.find_one({"script_id": project_data["script_id"]})
        if not audio_data:
            # Generate audio if not exists
            voice_response = await generate_voice(project_data["script_id"])
            audio_base64 = voice_response["audio_base64"]
            audio_duration = voice_response["duration"]
        else:
            audio_base64 = audio_data["audio_base64"]
            audio_duration = audio_data["duration"]
        
        # Assemble video
        video_base64 = await assemble_video(
            project_id=project_id,
            images=images_data,
            audio_base64=audio_base64,
            script_text=script_data["script_text"],
            duration=audio_duration
        )
        
        # Save video result
        video_result = VideoAssemblyResult(
            project_id=project_id,
            video_base64=video_base64,
            duration=audio_duration
        )
        
        await db.videos.insert_one(video_result.dict())
        
        # Update project status
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"status": "video_completed"}}
        )
        
        return {
            "video_id": video_result.id,
            "project_id": project_id,
            "duration": audio_duration,
            "resolution": "1080x1920",
            "video_base64": video_base64
        }
        
    except Exception as e:
        logger.error(f"Error assembling video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error assembling video: {str(e)}")

@api_router.post("/create-complete-video", response_model=dict)
async def create_complete_video(request: VideoGenerationRequest):
    """Complete pipeline: script -> images -> voice -> video assembly"""
    try:
        # Step 1: Generate script
        script_response = await generate_script(request)
        script_id = script_response.id
        
        # Step 2: Generate images
        images_response = await generate_images(script_id)
        
        # Step 3: Generate voice
        voice_response = await generate_voice(script_id)
        
        # Step 4: Create project
        project_obj = VideoProject(
            original_prompt=request.prompt,
            duration=request.duration,
            script_id=script_id,
            image_ids=[img.id for img in images_response["images"]],
            status="voice_completed"
        )
        
        await db.projects.insert_one(project_obj.dict())
        
        # Step 5: Assemble final video
        video_response = await assemble_final_video(project_obj.id)
        
        return {
            "project_id": project_obj.id,
            "script": script_response,
            "images": images_response["images"],
            "audio": {
                "audio_id": voice_response["audio_id"],
                "duration": voice_response["duration"],
                "voice_id": voice_response["voice_id"]
            },
            "video": {
                "video_id": video_response["video_id"],
                "duration": video_response["duration"],
                "resolution": video_response["resolution"],
                "video_base64": video_response["video_base64"]
            },
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error creating complete video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating complete video: {str(e)}")

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
        
        # Convert ObjectId to string for JSON serialization
        def convert_objectid(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == "_id" and hasattr(value, '__str__'):
                        data[key] = str(value)
                    elif isinstance(value, dict):
                        convert_objectid(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                convert_objectid(item)
            return data
        
        # Apply conversion to all data
        project_data = convert_objectid(project_data)
        if script_data:
            script_data = convert_objectid(script_data)
        for img in images_data:
            convert_objectid(img)
        
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



@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()