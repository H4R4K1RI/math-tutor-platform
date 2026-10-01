import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiPlus, FiTrash2 } from 'react-icons/fi';
import toast from 'react-hot-toast';

interface Question {
  text: string;
  type: string;
  points: number;
  order: number;
  correct_answer?: string;
  options: { text: string; is_correct: boolean; order: number }[];
}

interface TestData {
  title: string;
  description: string;
  time_limit: number | null;
  passing_score: number;
  group_id: number | null;
  student_id: number | null;
  questions: Question[];
}

const TestEditorPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isTeacher } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [groups, setGroups] = useState<{ id: number; name: string }[]>([]);
  const [students, setStudents] = useState<{ id: number; name: string }[]>([]);
  
  const [testData, setTestData] = useState<TestData>({
    title: '',
    description: '',
    time_limit: null,
    passing_score: 70,
    group_id: null,
    student_id: null,
    questions: []
  });

  useEffect(() => {
    if (!isTeacher) return;
    Promise.all([fetchGroups(), fetchStudents()]).catch(err => console.error('Error loading data:', err));
    if (id) fetchTest();
  }, [id, isTeacher]);

  const fetchGroups = async () => {
    try {
      const response = await apiClient.get('/groups');
      setGroups(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching groups:', error);
      setGroups([]);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/students');
      const studentsData = response.data.items || response.data;
      setStudents(Array.isArray(studentsData) ? studentsData : []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    }
  };

  const fetchTest = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/tests/${id}`);
      const data = response.data;
      setTestData({
        title: data.title,
        description: data.description || '',
        time_limit: data.time_limit,
        passing_score: data.passing_score,
        group_id: data.group_id,
        student_id: data.student_id,
        questions: data.questions.map((q: any, idx: number) => ({
          text: q.text,
          type: q.type,
          points: q.points,
          order: idx,
          correct_answer: q.correct_answer,
          options: (q.options || []).map((opt: any, optIdx: number) => ({
            text: opt.text,
            is_correct: opt.is_correct || false,
            order: optIdx
          }))
        }))
      });
    } catch (error) {
      console.error('Error fetching test:', error);
      toast.error('Ошибка при загрузке теста');
    } finally {
      setLoading(false);
    }
  };

  const addQuestion = () => {
    setTestData({
      ...testData,
      questions: [
        ...testData.questions,
        {
          text: '',
          type: 'single',
          points: 1,
          order: testData.questions.length,
          options: [
            { text: '', is_correct: false, order: 0 },
            { text: '', is_correct: false, order: 1 }
          ]
        }
      ]
    });
  };

  const updateQuestion = (index: number, field: string, value: any) => {
    const updatedQuestions = [...testData.questions];
    updatedQuestions[index] = { ...updatedQuestions[index], [field]: value };
    setTestData({ ...testData, questions: updatedQuestions });
  };

  const addOption = (qIndex: number) => {
    const updatedQuestions = [...testData.questions];
    updatedQuestions[qIndex].options.push({
      text: '',
      is_correct: false,
      order: updatedQuestions[qIndex].options.length
    });
    setTestData({ ...testData, questions: updatedQuestions });
  };

  const updateOption = (qIndex: number, optIndex: number, field: string, value: any) => {
    const updatedQuestions = [...testData.questions];
    updatedQuestions[qIndex].options[optIndex] = {
      ...updatedQuestions[qIndex].options[optIndex],
      [field]: value
    };
    setTestData({ ...testData, questions: updatedQuestions });
  };

  const removeOption = (qIndex: number, optIndex: number) => {
    const updatedQuestions = [...testData.questions];
    updatedQuestions[qIndex].options = updatedQuestions[qIndex].options.filter((_, i) => i !== optIndex);
    setTestData({ ...testData, questions: updatedQuestions });
  };

  const removeQuestion = (index: number) => {
    if (confirm('Удалить вопрос?')) {
      const updatedQuestions = testData.questions.filter((_, i) => i !== index);
      setTestData({ ...testData, questions: updatedQuestions });
    }
  };

  const saveTest = async () => {
    console.log('🔵 saveTest вызвана');
    
    if (!testData.title.trim()) {
      toast.error('Введите название теста');
      return;
    }
    if (testData.questions.length === 0) {
      toast.error('Добавьте хотя бы один вопрос');
      return;
    }

    setSaving(true);
    try {
      const cleanedData: any = {
        title: testData.title.trim(),
        description: testData.description?.trim() || null,
        time_limit: testData.time_limit ? Number(testData.time_limit) : null,
        passing_score: Number(testData.passing_score) || 70,
        group_id: testData.group_id ? Number(testData.group_id) : null,
        student_id: testData.student_id ? Number(testData.student_id) : null,
        questions: []
      };

      for (const q of testData.questions) {
        if (!q.text.trim()) {
          toast.error('У всех вопросов должен быть текст');
          setSaving(false);
          return;
        }

        const questionData: any = {
          text: q.text.trim(),
          type: q.type,
          points: Number(q.points) || 1,
          order: q.order,
        };

        if (q.type === 'open' || q.type === 'number') {
          questionData.correct_answer = q.correct_answer?.trim() || '';
          questionData.options = [];
        } else {
          const validOptions = q.options.filter(opt => opt.text.trim());
          if (validOptions.length < 2) {
            toast.error(`Для вопроса "${q.text}" нужно минимум 2 варианта ответа`);
            setSaving(false);
            return;
          }
          const hasCorrect = validOptions.some(opt => opt.is_correct);
          if (!hasCorrect) {
            toast.error(`Для вопроса "${q.text}" нужно отметить правильный вариант`);
            setSaving(false);
            return;
          }
          questionData.options = validOptions.map((opt, idx) => ({
            text: opt.text.trim(),
            is_correct: opt.is_correct,
            order: idx
          }));
        }
        cleanedData.questions.push(questionData);
      }

      console.log('Отправляемые данные:', cleanedData);

      if (id) {
        await apiClient.put(`/tests/${id}`, cleanedData);
      } else {
        await apiClient.post('/tests', cleanedData);
      }

      toast.success(id ? 'Тест обновлён' : 'Тест создан');
      navigate('/tests');
    } catch (error: any) {
      console.error('Save error:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при сохранении');
    } finally {
      setSaving(false);
    }
  };

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка...</p>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">{id ? 'Редактировать тест' : 'Создать тест'}</h1>
          <button
            type="button"
            onClick={saveTest}
            disabled={saving}
            className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium disabled:opacity-50"
          >
            {saving ? 'Сохранение...' : 'Сохранить тест'}
          </button>
        </div>

        <div className="bg-dark-card rounded-xl p-6 border border-white/10 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Основная информация</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Название теста</label>
              <input
                type="text"
                value={testData.title}
                onChange={(e) => setTestData({ ...testData, title: e.target.value })}
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                placeholder="Например: Квадратные уравнения"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Описание</label>
              <textarea
                value={testData.description}
                onChange={(e) => setTestData({ ...testData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                placeholder="Опишите тему теста, инструкции..."
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Ограничение времени (мин)</label>
                <input
                  type="number"
                  value={testData.time_limit || ''}
                  onChange={(e) => setTestData({ ...testData, time_limit: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  placeholder="Не ограничено"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Проходной балл (%)</label>
                <input
                  type="number"
                  value={testData.passing_score}
                  onChange={(e) => setTestData({ ...testData, passing_score: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  min="0"
                  max="100"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Назначить</label>
              <select
                value={testData.group_id ? `group_${testData.group_id}` : (testData.student_id ? `student_${testData.student_id}` : 'all')}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === 'all') {
                    setTestData({ ...testData, group_id: null, student_id: null });
                  } else if (val.startsWith('group_')) {
                    setTestData({ ...testData, group_id: parseInt(val.replace('group_', '')), student_id: null });
                  } else if (val.startsWith('student_')) {
                    setTestData({ ...testData, student_id: parseInt(val.replace('student_', '')), group_id: null });
                  }
                }}
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
              >
                <option value="all">📚 Для всех учеников</option>
                {groups.length > 0 && (
                  <optgroup label="👥 Группы">
                    {groups.map(g => (
                      <option key={`group_${g.id}`} value={`group_${g.id}`}>📁 {g.name}</option>
                    ))}
                  </optgroup>
                )}
                <optgroup label="👤 Конкретные ученики">
                  {Array.isArray(students) && students.map(s => (
                    <option key={`student_${s.id}`} value={`student_${s.id}`}>👤 {s.name}</option>
                  ))}
                </optgroup>
              </select>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-xl p-6 border border-white/10">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Вопросы</h2>
            <button
              type="button"
              onClick={addQuestion}
              className="px-3 py-1 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 transition flex items-center gap-1 text-sm"
            >
              <FiPlus size={14} />
              <span>Добавить вопрос</span>
            </button>
          </div>

          {testData.questions.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <p>Нет вопросов</p>
              <p className="text-sm">Нажмите "Добавить вопрос", чтобы начать</p>
            </div>
          ) : (
            <div className="space-y-4">
              {testData.questions.map((question, qIdx) => (
                <div key={qIdx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-white font-medium">Вопрос {qIdx + 1}</h3>
                    <button
                      type="button"
                      onClick={() => removeQuestion(qIdx)}
                      className="text-gray-400 hover:text-red-400 transition"
                    >
                      <FiTrash2 size={16} />
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={question.text}
                      onChange={(e) => updateQuestion(qIdx, 'text', e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white"
                      placeholder="Текст вопроса"
                    />
                    
                    <div className="grid grid-cols-2 gap-3">
                      <select
                        value={question.type}
                        onChange={(e) => updateQuestion(qIdx, 'type', e.target.value)}
                        className="px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white"
                      >
                        <option value="single">Одиночный выбор</option>
                        <option value="multiple">Множественный выбор</option>
                        <option value="number">Числовой ответ</option>
                        <option value="open">Открытый вопрос</option>
                      </select>
                      
                      <input
                        type="number"
                        value={question.points}
                        onChange={(e) => updateQuestion(qIdx, 'points', parseFloat(e.target.value) || 0)}
                        className="px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white"
                        placeholder="Баллы"
                        step="0.5"
                      />
                    </div>
                    
                    {(question.type === 'single' || question.type === 'multiple') && (
                      <div className="space-y-2">
                        <label className="text-sm text-gray-400">Варианты ответов</label>
                        {question.options.map((opt, optIdx) => (
                          <div key={optIdx} className="flex gap-2 items-center">
                            <input
                              type={question.type === 'single' ? 'radio' : 'checkbox'}
                              checked={opt.is_correct}
                              onChange={() => {
                                if (question.type === 'single') {
                                  const newOptions = question.options.map((o, i) => ({
                                    ...o,
                                    is_correct: i === optIdx
                                  }));
                                  updateQuestion(qIdx, 'options', newOptions);
                                } else {
                                  updateOption(qIdx, optIdx, 'is_correct', !opt.is_correct);
                                }
                              }}
                              className="w-4 h-4"
                            />
                            <input
                              type="text"
                              value={opt.text}
                              onChange={(e) => updateOption(qIdx, optIdx, 'text', e.target.value)}
                              className="flex-1 px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white"
                              placeholder="Вариант ответа"
                            />
                            <button
                              type="button"
                              onClick={() => removeOption(qIdx, optIdx)}
                              className="text-gray-400 hover:text-red-400 transition"
                            >
                              <FiTrash2 size={14} />
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addOption(qIdx)}
                          className="text-sm text-accent hover:text-accent/80 transition flex items-center gap-1"
                        >
                          <FiPlus size={12} />
                          <span>Добавить вариант</span>
                        </button>
                      </div>
                    )}
                    
                    {(question.type === 'number' || question.type === 'open') && (
                      <div>
                        <label className="block text-sm text-gray-400 mb-1">Правильный ответ</label>
                        <input
                          type="text"
                          value={question.correct_answer || ''}
                          onChange={(e) => updateQuestion(qIdx, 'correct_answer', e.target.value)}
                          className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white"
                          placeholder={question.type === 'number' ? 'Например: 42' : 'Пример правильного ответа'}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AnimatedPage>
  );
};

export default TestEditorPage;