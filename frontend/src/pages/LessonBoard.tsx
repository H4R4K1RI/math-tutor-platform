import React, { useEffect, useRef } from 'react';
import { Excalidraw } from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

interface LessonBoardProps {
  lessonId: number;
}

const LessonBoard: React.FC<LessonBoardProps> = ({ lessonId }) => {
  const ydocRef = useRef<Y.Doc | null>(null);
  const providerRef = useRef<WebsocketProvider | null>(null);
  const yElementsRef = useRef<Y.Map<any> | null>(null);
  const isRemoteRef = useRef(false);
  const apiRef = useRef<any>(null);
  const lastSerializedRef = useRef<string>('');

  // Инициализация Yjs
  useEffect(() => {
    const ydoc = new Y.Doc();
    ydocRef.current = ydoc;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/yjs`;

    const provider = new WebsocketProvider(wsUrl, `lesson-${lessonId}`, ydoc);
    providerRef.current = provider;

    yElementsRef.current = ydoc.getMap('elements');

    provider.on('status', (event: { status: string }) => {
      console.log('[yjs]', event.status);
    });

    const yElements = yElementsRef.current;
    const applyRemote = () => {
      if (!apiRef.current) return;
      // Устанавливаем флаг + НЕ сбрасываем синхронно — ждём микротаск + рендер
      isRemoteRef.current = true;
      const elements = Array.from(yElements.values());
      apiRef.current.updateScene({ elements });
      // Снимаем флаг только после того, как React обработает изменение
      setTimeout(() => {
        isRemoteRef.current = false;
      }, 0);
    };

    yElements.observe(applyRemote);

    return () => {
      yElements.unobserve(applyRemote);
      provider.destroy();
      ydoc.destroy();
    };
  }, [lessonId]);

  return (
    <div style={{ position: 'fixed', inset: 0, paddingTop: '60px' }}>
      <Excalidraw
        excalidrawAPI={(api) => {
          apiRef.current = api;
        }}
        onChange={(elements) => {
          if (isRemoteRef.current) return;
          const yElements = yElementsRef.current;
          const ydoc = ydocRef.current;
          if (!yElements || !ydoc) return;

          // Дополнительная защита: сравниваем сериализацию
          const serialized = JSON.stringify(
            elements.map((el) => ({ id: el.id, v: el.version }))
          );
          if (serialized === lastSerializedRef.current) return;
          lastSerializedRef.current = serialized;

          ydoc.transact(() => {
            const currentIds = new Set(elements.map((el) => el.id));
            for (const key of Array.from(yElements.keys())) {
              if (!currentIds.has(key)) yElements.delete(key);
            }
            elements.forEach((el) => {
              yElements.set(el.id, el);
            });
          });
        }}
        initialData={{
          elements: [],
          appState: { viewBackgroundColor: '#ffffff' },
        }}
        UIOptions={{
          canvasActions: {
            saveToActiveFile: false,
            loadScene: false,
            export: false,
          },
        }}
      />
    </div>
  );
};

export default LessonBoard;