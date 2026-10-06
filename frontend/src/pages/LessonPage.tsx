import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiVideo, FiEdit3, FiMessageCircle, FiArrowLeft } from 'react-icons/fi';
import LessonVideo from './LessonVideo';
import LessonBoard from './LessonBoard';

type Tab = 'video' | 'board' | 'chat';

const LessonPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<Tab>('video');
  const lessonId = parseInt(id || '0');

  if (!lessonId) {
    return (
      <div className="flex items-center justify-center h-screen text-white">
        <p>Некорректный ID урока</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-dark-bg">
      {/* Header */}
      <div className="bg-dark-card border-b border-white/10 px-4 py-3 flex items-center gap-4 flex-shrink-0">
        <button
          onClick={() => navigate('/calendar')}
          className="p-2 rounded-lg hover:bg-white/10 text-gray-300 transition"
          aria-label="Назад"
        >
          <FiArrowLeft size={20} />
        </button>

        <div className="flex-1">
          <h1 className="text-lg font-semibold text-white">
            Урок #{lessonId}
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-white/5 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('video')}
            className={`px-4 py-1.5 rounded-md transition flex items-center gap-2 text-sm ${
              activeTab === 'video'
                ? 'bg-accent text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <FiVideo size={16} />
            <span>Видео</span>
          </button>
          <button
            onClick={() => setActiveTab('board')}
            className={`px-4 py-1.5 rounded-md transition flex items-center gap-2 text-sm ${
              activeTab === 'board'
                ? 'bg-accent text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <FiEdit3 size={16} />
            <span>Доска</span>
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-1.5 rounded-md transition flex items-center gap-2 text-sm ${
              activeTab === 'chat'
                ? 'bg-accent text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            <FiMessageCircle size={16} />
            <span>Чат</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'video' && <LessonVideo lessonId={lessonId} />}
        {activeTab === 'board' && <LessonBoard lessonId={lessonId} />}
        {activeTab === 'chat' && (
          <div className="flex items-center justify-center h-full text-white">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-gray-400 mb-4">
                Чат урока доступен на отдельной странице
              </p>
              <button
                onClick={() => navigate(`/chat/${lessonId}`)}
                className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition"
              >
                Открыть чат урока
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LessonPage;