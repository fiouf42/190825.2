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

  const generateVideo = async () => {
    if (!prompt.trim()) {
      setError("Veuillez entrer un prompt");
      return;
    }

    setLoading(true);
    setError("");
    setProject(null);

    try {
      const response = await axios.post(`${API}/create-video-project`, {
        prompt: prompt.trim(),
        duration: duration
      });

      const projectId = response.data.id;
      
      // Get project details
      const projectResponse = await axios.get(`${API}/project/${projectId}`);
      setProject(projectResponse.data);
      
    } catch (err) {
      console.error("Error:", err);
      setError(err.response?.data?.detail || "Erreur lors de la génération");
    } finally {
      setLoading(false);
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
              Transformez vos idées en vidéos TikTok captivantes avec des scripts intelligents et des visuels au style charbon dramatique
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Input Form */}
          <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl mb-12">
            <h2 className="text-2xl font-bold text-white mb-6">Générer votre vidéo</h2>
            
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

              <button
                onClick={generateVideo}
                disabled={loading || !prompt.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 px-8 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                    Génération en cours...
                  </div>
                ) : (
                  "Générer la vidéo"
                )}
              </button>

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
              {/* Script Section */}
              <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                <h3 className="text-2xl font-bold text-white mb-6">Script généré</h3>
                <div className="bg-gray-900 rounded-xl p-6 border border-gray-600">
                  <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {project.script?.script_text}
                  </p>
                </div>
                
                {project.script?.scenes && project.script.scenes.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold text-white mb-4">Scènes</h4>
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

              {/* Images Section */}
              {project.images && project.images.length > 0 && (
                <div className="bg-gray-800 bg-opacity-80 backdrop-blur-sm rounded-2xl p-8 border border-gray-700 shadow-2xl">
                  <h3 className="text-2xl font-bold text-white mb-6">Visuels générés (Style Charbon)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {project.images.map((image, index) => (
                      <div key={image.id} className="bg-gray-900 rounded-xl overflow-hidden border border-gray-600">
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

              {/* Next Steps */}
              <div className="bg-gradient-to-r from-blue-900 to-purple-900 bg-opacity-50 rounded-2xl p-8 border border-blue-800">
                <h3 className="text-2xl font-bold text-white mb-4">Prochaines étapes</h3>
                <div className="text-blue-200">
                  <p className="mb-3">✅ Script créé avec {project.script?.scenes?.length || 0} scènes</p>
                  <p className="mb-3">✅ {project.images?.length || 0} visuels générés au style charbon</p>
                  <p className="text-gray-400">🔄 Narration vocale (à venir)</p>
                  <p className="text-gray-400">🔄 Montage vidéo automatique (à venir)</p>
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