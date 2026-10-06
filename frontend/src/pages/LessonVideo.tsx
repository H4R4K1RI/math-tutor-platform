import React, { useEffect, useState } from 'react';
import { JitsiMeeting } from '@jitsi/react-sdk';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

interface LessonVideoProps {
  lessonId: number;
}

interface VideoTokenResponse {
  token: string;
  domain: string;
  room: string;
}

const LessonVideo: React.FC<LessonVideoProps> = ({ lessonId }) => {
  const { user } = useAuth();
  const [videoInfo, setVideoInfo] = useState<VideoTokenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchToken = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.post<VideoTokenResponse>(
          `/video/token/${lessonId}`
        );
        setVideoInfo(response.data);
      } catch (err: any) {
        console.error('Error fetching Jitsi token:', err);
        const detail = err.response?.data?.detail;
        setError(detail || 'Не удалось получить доступ к видео');
        toast.error(detail || 'Ошибка загрузки видео');
      } finally {
        setLoading(false);
      }
    };

    fetchToken();
  }, [lessonId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p>Подключение к видео...</p>
        </div>
      </div>
    );
  }

  if (error || !videoInfo) {
    return (
      <div className="flex items-center justify-center h-full text-white">
        <div className="text-center">
          <div className="text-6xl mb-4">🚫</div>
          <p className="text-lg">{error || 'Видео недоступно'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-black">
      <JitsiMeeting
        domain={videoInfo.domain}
        roomName={videoInfo.room}
        jwt={videoInfo.token}
        configOverwrite={{
          startWithAudioMuted: false,
          startWithVideoMuted: false,
          prejoinPageEnabled: false,
          disableModeratorIndicator: false,
        }}
        interfaceConfigOverwrite={{
          SHOW_JITSI_WATERMARK: false,
          SHOW_BRAND_WATERMARK: false,
          DEFAULT_BACKGROUND: '#0a0a0a',
          TOOLBAR_BUTTONS: [
            'microphone',
            'camera',
            'desktop',
            'chat',
            'raisehand',
            'participants-pane',
            'tileview',
            'fullscreen',
            'settings',
            'hangup',
          ],
        }}
        userInfo={{
          displayName: user?.full_name || 'Пользователь',
          email: user?.email || '',
        }}
        onApiReady={(api) => {
          console.log('Jitsi API ready', api);
        }}
        getIFrameRef={(iframeRef) => {
          iframeRef.style.height = '100%';
          iframeRef.style.width = '100%';
          iframeRef.style.border = '0';
        }}
      />
    </div>
  );
};

export default LessonVideo;