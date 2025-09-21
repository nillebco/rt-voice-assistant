import "./App.css";
import { useState } from "react";
import Transcribe from "./Transcribe";
import Assistant from "./Assistant";

type TabType = 'transcribe' | 'assistant';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('transcribe');

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'transcribe':
        return <Transcribe />;
      case 'assistant':
        return <Assistant />;
      default:
        return <Transcribe />;
    }
  };

  return (
    <div className="app">
      <div className="tab-container">
        <div className="tab-header">
          <button
            className={`tab-button ${activeTab === 'transcribe' ? 'active' : ''}`}
            onClick={() => setActiveTab('transcribe')}
          >
            📝 Transcribe
          </button>
          <button
            className={`tab-button ${activeTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setActiveTab('assistant')}
          >
            🤖 Assistant
          </button>
        </div>
        <div className="tab-content">
          {renderActiveTab()}
        </div>
      </div>
    </div>
  );
}

export default App;
