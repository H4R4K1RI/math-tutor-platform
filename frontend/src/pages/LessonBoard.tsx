import React from 'react';

interface LessonBoardProps {
  lessonId: number;
}

const LessonBoard: React.FC<LessonBoardProps> = ({ lessonId }) => {
  return (
    <div className="flex items-center justify-center h-full text-white bg-dark-bg">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4">✏️</div>
        <h2 className="text-2xl font-bold mb-3">Онлайн-доска</h2>
        <p className="text-gray-400 mb-6">
          Совместная доска для рисования появится здесь совсем скоро.
          Урок #{lessonId}.
        </p>
        <div className="inline-block px-4 py-2 rounded-lg bg-accent/20 text-accent text-sm">
          Скоро
        </div>
      </div>
    </div>
  );
};

export default LessonBoard;