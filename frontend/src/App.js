import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(30);
  const [loading, setLoading] = useState(false);
  const [project, setProject] = useState(null);
  const [error, setError] = useState("");
  const [generationStep, setGenerationStep] = useState("");
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState("");

  // Load available voices on component mount
  React.useEffect(() => {
    loadAvailableVoices();
  }, []);

  const loadAvailableVoices = async () => {
    try {
      const response = await axios.get(`${API}/voices/available`);
      setAvailableVoices(response.data.voices || []);
      // Auto-select first French or good voice
      const frenchVoice = response.data.voices?.find(v => 
        v.name.toLowerCase().includes('nicolas') || 
        v.name.toLowerCase().includes('adam') ||
        v.labels?.accent?.includes('french')
      );
      if (frenchVoice) {
        setSelectedVoice(frenchVoice.voice_id);
      } else if (response.data.voices?.length > 0) {
        setSelectedVoice(response.data.voices[0].voice_id);
      }
    } catch (err) {
      console.error("Error loading voices:", err);
    }
  };

  const generateCompleteVideo = async () => {
    if (!prompt.trim()) {
      setError("Veuillez entrer un prompt");
      return;
    }

    if (!selectedVoice) {
      setError("Veuillez sélectionner une voix");
      return;
    }

    setLoading(true);
    setError("");
    setProject(null);
    setGenerationStep("Initialisation...");

    try {
      // Call the complete video pipeline endpoint
      setGenerationStep("🎬 Génération du script...");
      await new Promise(resolve => setTimeout(resolve, 500)); // Visual feedback
      
      setGenerationStep("🎨 Création des visuels...");
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setGenerationStep("🎵 Génération de la voix...");
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setGenerationStep("🎞️ Assemblage de la vidéo...");
      
      const response = await axios.post(`${API}/create-complete-video`, {
        prompt: prompt.trim(),
        duration: duration,
        voice_id: selectedVoice
      });

      setProject(response.data);
      setGenerationStep("✅ Vidéo générée avec succès!");
      
    } catch (err) {
      console.error("Error:", err);
      // Améliorer l'affichage d'erreur avec plus de détails
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          "Erreur lors de la génération de la vidéo";
      
      // Log plus détaillé pour le débogage
      console.error("Error details:", {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
      
      setError(errorMessage);
      setGenerationStep("");
    } finally {
      setLoading(false);
    }
  };

  const downloadVideo = () => {
    if (project?.video?.video_base64) {
      const link = document.createElement('a');
      link.href = `data:video/mp4;base64,${project.video.video_base64}`;
      link.download = `tiktok-video-${Date.now()}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1577327966244-999949c7e884?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHx2aWRlbyUyMGNyZWF0aW9ufGVufDB8fHxibGFja19hbmRfd2hpdGV8MTc1Mzc4NDM3NHww&ixlib=rb-4.1.0&q=85')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
        <div className="absolute inset-0 bg-black bg-opacity-60" />
        
        <div className="relative z-10 container mx-auto px-6 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
              Créateur TikTok
              <span className="block text-gray-300 text-4xl md:text-5xl font-light mt-2">
                Alimenté par l'IA
              </span>
            </h1>
            <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
              Transformez vos idées en vidéos TikTok captivantes avec des scripts intelligents, des visuels au style charbon dramatique et une narration vocale professionnelle
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Input Form */}
          <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl mb-12">
            <h2 className="text-2xl font-bold text-white mb-6">Générer votre vidéo TikTok complète</h2>
            
            <div className="space-y-6">
              <div>
                <label className="block text-gray-300 text-sm font-medium mb-3">
                  Décrivez votre idée de vidéo
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Ex: Une vidéo sur les astuces de productivité pour étudiants..."
                  className="w-full h-32 px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              <div>
                <label className="block text-gray-300 text-sm font-medium mb-3">
                  Durée de la vidéo: {duration}s
                </label>
                <input
                  type="range"
                  min="15"
                  max="60"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-gray-500 text-sm mt-1">
                  <span>15s</span>
                  <span>60s</span>
                </div>
              </div>

              {availableVoices.length > 0 && (
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-3">
                    Voix de narration ({availableVoices.length} disponibles)
                  </label>
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-600 rounded-xl text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {availableVoices.map((voice) => (
                      <option key={voice.voice_id} value={voice.voice_id}>
                        {voice.name}
                        {voice.labels?.gender && ` - ${voice.labels.gender}`}
                        {voice.labels?.accent && ` (${voice.labels.accent})`}
                        {voice.labels?.age && ` - ${voice.labels.age}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <button
                onClick={generateCompleteVideo}
                disabled={loading || !prompt.trim() || !selectedVoice}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-8 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                    Génération en cours...
                  </div>
                ) : (
                  "🎬 Générer la vidéo complète"
                )}
              </button>

              {generationStep && (
                <div className="bg-blue-900 bg-opacity-50 border border-blue-600 text-blue-200 px-4 py-3 rounded-lg">
                  <div className="flex items-center">
                    <div className="animate-pulse mr-3">⚡</div>
                    {generationStep}
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-900 bg-opacity-50 border border-red-600 text-red-200 px-4 py-3 rounded-lg">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Results */}
          {project && (
            <div className="space-y-8">
              {/* Video Result */}
              {project.video && (
                <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-2xl font-bold text-white">🎬 Votre vidéo TikTok</h3>
                    <button
                      onClick={downloadVideo}
                      className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition-colors duration-200 flex items-center"
                    >
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Télécharger MP4
                    </button>
                  </div>
                  
                  <div className="bg-gray-900 rounded-xl overflow-hidden">
                    {project.video.video_base64 ? (
                      <video
                        controls
                        className="w-full max-w-sm mx-auto"
                        style={{ aspectRatio: '9/16' }}
                      >
                        <source src={`data:video/mp4;base64,${project.video.video_base64}`} type="video/mp4" />
                        Votre navigateur ne supporte pas la lecture vidéo.
                      </video>
                    ) : (
                      <div className="aspect-[9/16] max-w-sm mx-auto bg-gray-700 flex items-center justify-center">
                        <p className="text-gray-400">Vidéo non disponible</p>
                      </div>
                    )}
                    
                    <div className="p-4">
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Résolution:</span>
                          <p className="text-white font-medium">{project.video.resolution || '1080x1920'}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Durée:</span>
                          <p className="text-white font-medium">{project.video.duration || duration}s</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Format:</span>
                          <p className="text-white font-medium">MP4 (TikTok)</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Script Section */}
              {project.script && (
                <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6">📝 Script généré (GPT-4.1)</h3>
                  <div className="bg-gray-900 rounded-xl p-6 border border-gray-600">
                    <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {project.script.script_text}
                    </p>
                  </div>
                  
                  {project.script.scenes && project.script.scenes.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-lg font-semibold text-white mb-4">🎬 Scènes ({project.script.scenes.length})</h4>
                      <div className="space-y-3">
                        {project.script.scenes.map((scene, index) => (
                          <div key={index} className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                            <span className="text-blue-400 font-medium">Scène {index + 1}:</span>
                            <p className="text-gray-300 mt-1">{scene}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Images Section */}
              {project.images && project.images.length > 0 && (
                <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6">🎨 Visuels générés - Style Charbon ({project.images.length})</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {project.images.map((image, index) => (
                      <div key={image.id || index} className="bg-gray-900 rounded-xl overflow-hidden border border-gray-600">
                        <img
                          src={`data:image/png;base64,${image.image_base64}`}
                          alt={`Scène ${index + 1}`}
                          className="w-full h-64 object-cover"
                        />
                        <div className="p-4">
                          <h4 className="text-white font-medium mb-2">Scène {index + 1}</h4>
                          <p className="text-gray-400 text-sm">{image.scene_description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Audio Section */}
              {project.audio && (
                <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6">🎵 Narration vocale (ElevenLabs)</h3>
                  <div className="bg-gray-900 rounded-xl p-6 border border-gray-600">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <span className="text-gray-400">Durée:</span>
                        <p className="text-white font-medium">{project.audio.duration}s</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Voix:</span>
                        <p className="text-white font-medium">{project.audio.voice_id}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Pipeline Summary */}
              <div className="bg-gradient-to-r from-green-900 to-blue-900 bg-opacity-50 rounded-2xl p-8 border border-green-800">
                <h3 className="text-2xl font-bold text-white mb-4">✅ Pipeline de génération terminé</h3>
                <div className="text-green-200 space-y-2">
                  <p className="flex items-center"><span className="mr-2">✅</span> Script créé avec GPT-4.1 ({project.script?.scenes?.length || 0} scènes)</p>
                  <p className="flex items-center"><span className="mr-2">✅</span> {project.images?.length || 0} visuels générés au style charbon</p>
                  <p className="flex items-center"><span className="mr-2">✅</span> Narration vocale avec ElevenLabs</p>
                  <p className="flex items-center"><span className="mr-2">✅</span> Montage vidéo automatique avec FFmpeg</p>
                  <p className="flex items-center"><span className="mr-2">🎬</span> <strong>Vidéo TikTok finale générée!</strong></p>
                </div>
                
                <div className="mt-6 p-4 bg-gray-800 bg-opacity-50 rounded-lg">
                  <h4 className="text-white font-semibold mb-2">Caractéristiques techniques:</h4>
                  <ul className="text-sm text-gray-300 space-y-1">
                    <li>• Format: MP4 optimisé pour TikTok (1080x1920)</li>
                    <li>• Durée: {duration} secondes</li>
                    <li>• Transitions: Fondu enchaîné automatique</li>
                    <li>• Sous-titres: Style TikTok intégré</li>
                    <li>• Audio: Narration vocale professionnelle</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;