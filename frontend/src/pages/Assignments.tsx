import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { Assignment, User } from '../types';
import toast from 'react-hot-toast';
const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8000';
const Assignments: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [fileUrl, setFileUrl] = useState('');
  const [existingFileUrl, setExistingFileUrl] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    student_id: null as number | null,
  });

  useEffect(() => {
    fetchAssignments();
    fetchStudents();
  }, []);

  const fetchAssignments = async () => {
    const response = await apiClient.get('/assignments');
    setAssignments(response.data);
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/users/students');
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    setFileUrl(response.data.url);
    toast.success('✅ Файл загружен!');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const attachmentsValue = fileUrl 
        ? `["${fileUrl}"]` 
        : (existingFileUrl || null);
    
      const submitData = {
        title: formData.title,
        description: formData.description,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        student_id: formData.student_id,
        attachments: attachmentsValue
      };
      
      if (editingId) {
        await apiClient.put(`/assignments/${editingId}`, submitData);
        toast.success('✅ Задание обновлено!');
      } else {
        await apiClient.post('/assignments', submitData);
        toast.success('✅ Задание создано!');
      }
      setShowForm(false);
      setEditingId(null);
      setFileUrl('');
      setExistingFileUrl('');
      setFormData({ title: '', description: '', due_date: '', student_id: null });
      fetchAssignments();
    } catch (error: any) {
      console.error('Error saving assignment:', error);
      toast.error('❌ Ошибка при сохранении');
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Удалить задание?')) {
      await apiClient.delete(`/assignments/${id}`);
      fetchAssignments();
    }
  };

  const handleEdit = (assignment: Assignment) => {
    setEditingId(assignment.id);
    setFormData({
      title: assignment.title,
      description: assignment.description,
      due_date: assignment.due_date ? assignment.due_date.slice(0, 16) : '',
      student_id: assignment.student_id,
    });
    
    if (assignment.attachments && assignment.attachments !== 'null' && assignment.attachments !== '[]') {
      try {
        const files = JSON.parse(assignment.attachments);
        if (Array.isArray(files) && files.length > 0) {
          setExistingFileUrl(assignment.attachments);
        } else {
          setExistingFileUrl('');
        }
      } catch (e) {
        console.error('Error parsing attachments:', e);
        setExistingFileUrl('');
      }
    } else {
      setExistingFileUrl('');
    }
    
    setShowForm(true);
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Управление заданиями</h1>
        <button
          onClick={() => { setShowForm(true); setEditingId(null); setFormData({ title: '', description: '', due_date: '', student_id: null }); setFileUrl(''); setExistingFileUrl(''); }}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Создать задание
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{editingId ? 'Редактировать задание' : 'Создать задание'}</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Название</label>
              <input
                type="text"
                placeholder="Название"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full border rounded p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание</label>
              <textarea
                placeholder="Описание"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded p-2"
                rows={4}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Дедлайн</label>
              <input
                type="datetime-local"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full border rounded p-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Прикрепить файл</label>
              <input type="file" onChange={handleFileUpload} className="border rounded p-1" />
              {fileUrl && <p className="text-green-600 text-sm mt-1">✅ Файл загружен</p>}
              
              {existingFileUrl && (
                <div className="mt-2 p-2 bg-gray-50 rounded">
                  <p className="text-sm text-gray-600 font-medium">Текущий файл:</p>
                  <a 
                    href={`${SERVER_URL}${JSON.parse(existingFileUrl)[0]}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm"
                  >
                    📎 Скачать текущий файл
                  </a>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Назначить ученику</label>
              <select
                value={formData.student_id === null ? "all" : formData.student_id}
                onChange={(e) => {
                  const value = e.target.value;
                  setFormData({ ...formData, student_id: value === "all" ? null : parseInt(value) });
                }}
                className="w-full border rounded p-2"
              >
                <option value="all">📚 Для всех учеников</option>
                {students.map(student => (
                  <option key={student.id} value={student.id}>
                    👤 {student.full_name} ({student.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-x-2">
              <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                {editingId ? 'Обновить' : 'Создать'}
              </button>
              <button 
                type="button" 
                onClick={() => { setShowForm(false); setEditingId(null); setFileUrl(''); setExistingFileUrl(''); }} 
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        {assignments.length === 0 ? (
          <p className="p-4 text-gray-500">Нет заданий</p>
        ) : (
          assignments.map(assignment => (
            <div key={assignment.id} className="border-b p-4 hover:bg-gray-50">
              <h3 className="font-semibold text-lg">{assignment.title}</h3>
              <p className="text-gray-600 mt-1">{assignment.description}</p>
              <p className="text-sm text-gray-500 mt-2">
                Дедлайн: {new Date(assignment.due_date).toLocaleString()}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {assignment.student_id === null ? (
                  <span className="text-blue-600">📚 Для всех учеников</span>
                ) : (
                  <span>👤 Для ученика ID: {assignment.student_id}</span>
                )}
              </p>
              {assignment.attachments && (
                <p className="text-sm text-blue-600 mt-1">📎 Есть вложение</p>
              )}
              <div className="mt-3 space-x-2">
                <button onClick={() => handleEdit(assignment)} className="text-blue-600 hover:underline">Редактировать</button>
                <button onClick={() => handleDelete(assignment.id)} className="text-red-600 hover:underline">Удалить</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Assignments;