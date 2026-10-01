import React, { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { Assignment, User } from '../types';
import toast from 'react-hot-toast';
import Pagination from '../components/Pagination';
import { socket } from '../socket';

interface Group {
  id: number;
  name: string;
  description: string | null;
  student_count: number;
}

const Assignments: React.FC = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [attachmentUrls, setAttachmentUrls] = useState<string[]>([]);
  const [existingAttachmentUrls, setExistingAttachmentUrls] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    student_id: null as number | null,
    group_id: null as number | null,
  });

  const [skip, setSkip] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 10;

  const fetchAssignments = async () => {
    try {
      const response = await apiClient.get('/assignments', { params: { skip, limit } });
      setAssignments(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Error fetching assignments:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/users/students');
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await apiClient.get('/groups');
      setGroups(response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  useEffect(() => {
    fetchAssignments();
    fetchStudents();
    fetchGroups();
  }, [skip]);

  useEffect(() => {
    const handleAssignmentUpdate = () => fetchAssignments();
    if (socket) {
      socket.on('assignment_updated', handleAssignmentUpdate);
      socket.on('assignment_deleted', handleAssignmentUpdate);
    }
    return () => {
      if (socket) {
        socket.off('assignment_updated', handleAssignmentUpdate);
        socket.off('assignment_deleted', handleAssignmentUpdate);
      }
    };
  }, [skip]);

  const handleMultipleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newUrls: string[] = [];
    for (const file of Array.from(files)) {
      const formDataFile = new FormData();
      formDataFile.append('file', file);
      const response = await apiClient.post('/upload', formDataFile, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      newUrls.push(response.data.url);
    }
    setAttachmentUrls((prev) => [...prev, ...newUrls]);
    toast.success(`Загружено файлов: ${newUrls.length}`);
  };

  const removeAttachment = (index: number) => {
    setAttachmentUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const removeExistingAttachment = (index: number) => {
    setExistingAttachmentUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    if (!formData.title.trim()) {
      toast.error('Введите название задания');
      return false;
    }
    if (formData.title.trim().length < 3) {
      toast.error('Название должно быть не менее 3 символов');
      return false;
    }
    if (!formData.description.trim()) {
      toast.error('Введите описание задания');
      return false;
    }
    if (!formData.due_date) {
      toast.error('Выберите дату дедлайна');
      return false;
    }
    if (new Date(formData.due_date) < new Date()) {
      toast.error('Дедлайн не может быть в прошлом');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      const allAttachments = [...existingAttachmentUrls, ...attachmentUrls].filter((url) => url);
      const attachmentsValue = allAttachments.length > 0 ? JSON.stringify(allAttachments) : null;

      const submitData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        student_id: formData.student_id,
        group_id: formData.group_id,
        attachments: attachmentsValue,
      };

      if (editingId) {
        await apiClient.put(`/assignments/${editingId}`, submitData);
        toast.success('✅ Задание обновлено!');
      } else {
        const response = await apiClient.post('/assignments', submitData);
        const count = response.data?.count || 1;
        if (count > 1) {
          toast.success(`✅ Создано заданий: ${count}`);
        } else {
          toast.success('✅ Задание создано!');
        }
      }
      setShowForm(false);
      setEditingId(null);
      setAttachmentUrls([]);
      setExistingAttachmentUrls([]);
      setFormData({ title: '', description: '', due_date: '', student_id: null, group_id: null });
      fetchAssignments();
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      let message = '❌ Ошибка при сохранении';

      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((e: any) => `${(e.loc || []).join('.')}: ${e.msg}`)
          .join('; ');
      }

      toast.error(message);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm('Удалить задание?')) {
      try {
        await apiClient.delete(`/assignments/${id}`);
        toast.success('Задание удалено');
        fetchAssignments();
      } catch (error: any) {
        const detail = error.response?.data?.detail;
        let message = '❌ Ошибка при удалении';
        if (typeof detail === 'string') {
          message = detail;
        } else if (Array.isArray(detail)) {
          message = detail
            .map((e: any) => `${(e.loc || []).join('.')}: ${e.msg}`)
            .join('; ');
        }
        toast.error(message);
      }
    }
  };

  const handleEdit = (assignment: Assignment) => {
    setEditingId(assignment.id);
    setFormData({
      title: assignment.title,
      description: assignment.description,
      due_date: assignment.due_date ? assignment.due_date.slice(0, 16) : '',
      student_id: assignment.student_id,
      group_id: null,
    });

    if (assignment.attachments) {
      try {
        const files = JSON.parse(assignment.attachments);
        setExistingAttachmentUrls(Array.isArray(files) ? files.filter((url: string) => url) : []);
      } catch (e) {
        setExistingAttachmentUrls([]);
      }
    } else {
      setExistingAttachmentUrls([]);
    }
    setAttachmentUrls([]);
    setShowForm(true);

    setTimeout(() => {
      document.getElementById('assignment-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const getSelectedValue = () => {
    if (formData.group_id) return `group_${formData.group_id}`;
    if (formData.student_id !== null) return `student_${formData.student_id}`;
    return 'all';
  };

  const SERVER_URL = '';

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold dark:text-white">Управление заданиями</h1>
        <button
          onClick={() => {
            setShowForm(true);
            setEditingId(null);
            setFormData({ title: '', description: '', due_date: '', student_id: null, group_id: null });
            setAttachmentUrls([]);
            setExistingAttachmentUrls([]);
          }}
          className="border border-[#2e7d5e] text-[#2e7d5e] hover:bg-[#2e7d5e] hover:text-white font-semibold px-4 py-2 rounded-lg transition bg-transparent"
        >
          + Создать задание
        </button>
      </div>

      {showForm && (
        <div id="assignment-form" className="bg-white dark:bg-[#1a1a1a] rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 dark:text-white">
            {editingId ? 'Редактировать задание' : 'Создать задание'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Название *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full border rounded-lg p-2 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Описание *
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full border rounded-lg p-2 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
                rows={4}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Дедлайн *
              </label>
              <input
                type="datetime-local"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full border rounded-lg p-2 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Назначить
              </label>
              <select
                value={getSelectedValue()}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === 'all') {
                    setFormData({ ...formData, student_id: null, group_id: null });
                  } else if (value.startsWith('group_')) {
                    setFormData({
                      ...formData,
                      student_id: null,
                      group_id: parseInt(value.replace('group_', '')),
                    });
                  } else if (value.startsWith('student_')) {
                    setFormData({
                      ...formData,
                      student_id: parseInt(value.replace('student_', '')),
                      group_id: null,
                    });
                  }
                }}
                className="w-full border rounded-lg p-2 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
              >
                <option value="all">📚 Для всех учеников</option>
                {groups.length > 0 && (
                  <optgroup label="👥 Группы">
                    {groups.map((group) => (
                      <option key={`group_${group.id}`} value={`group_${group.id}`}>
                        📁 {group.name} ({group.student_count} учеников)
                      </option>
                    ))}
                  </optgroup>
                )}
                <optgroup label="👤 Конкретные ученики">
                  {students.map((student) => (
                    <option key={`student_${student.id}`} value={`student_${student.id}`}>
                      👤 {student.full_name} ({student.email})
                    </option>
                  ))}
                </optgroup>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Прикрепить файлы (можно несколько)
              </label>
              <input
                type="file"
                multiple
                onChange={handleMultipleFileUpload}
                className="border rounded-lg p-1 dark:bg-[#2a2a2a] dark:border-gray-600 dark:text-white"
              />

              {existingAttachmentUrls && existingAttachmentUrls.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Текущие файлы:</p>
                  {existingAttachmentUrls
                    .filter((url) => url)
                    .map((url, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-gray-50 dark:bg-[#2a2a2a] p-2 rounded mt-1"
                      >
                        <a
                          href={`${SERVER_URL}${url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#2e7d5e] dark:text-[#4a9b6e] text-sm break-all"
                        >
                          📎 Файл {idx + 1}
                        </a>
                        <button
                          type="button"
                          onClick={() => removeExistingAttachment(idx)}
                          className="text-red-500 text-sm hover:text-red-700"
                        >
                          ✖ Удалить
                        </button>
                      </div>
                    ))}
                </div>
              )}

              {attachmentUrls && attachmentUrls.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Новые файлы:</p>
                  {attachmentUrls
                    .filter((url) => url)
                    .map((url, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-gray-50 dark:bg-[#2a2a2a] p-2 rounded mt-1"
                      >
                        <a
                          href={`${SERVER_URL}${url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#2e7d5e] dark:text-[#4a9b6e] text-sm break-all"
                        >
                          📎 Новый файл {idx + 1}
                        </a>
                        <button
                          type="button"
                          onClick={() => removeAttachment(idx)}
                          className="text-red-500 text-sm hover:text-red-700"
                        >
                          ✖ Удалить
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>

            <div className="space-x-2">
              <button
                type="submit"
                className="bg-[#2e7d5e] hover:bg-[#1e5a44] text-white px-4 py-2 rounded-lg transition"
              >
                {editingId ? 'Обновить' : 'Создать'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  setAttachmentUrls([]);
                  setExistingAttachmentUrls([]);
                }}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white dark:bg-[#1a1a1a] rounded-lg shadow">
        {assignments.length === 0 ? (
          <p className="p-4 text-gray-500 dark:text-gray-400">Нет заданий</p>
        ) : (
          assignments.map((assignment) => (
            <div
              key={assignment.id}
              className="border-b border-gray-200 dark:border-gray-700 p-4 hover:bg-gray-100 dark:hover:bg-[#1a2a1a] transition-colors duration-200"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg dark:text-white">{assignment.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400 mt-1">{assignment.description}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                    Дедлайн: {new Date(assignment.due_date).toLocaleString()}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                    {assignment.student_id === null ? (
                      <span className="text-blue-600 dark:text-[#4a9b6e]">📚 Для всех учеников</span>
                    ) : (
                      <span>👤 Для ученика ID: {assignment.student_id}</span>
                    )}
                  </p>
                  {assignment.attachments && (
                    <p className="text-sm text-blue-600 dark:text-[#4a9b6e] mt-1">📎 Есть вложения</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(assignment)}
                    className="text-blue-600 dark:text-[#4a9b6e] hover:underline"
                  >
                    Редактировать
                  </button>
                  <button
                    onClick={() => handleDelete(assignment.id)}
                    className="text-red-600 dark:text-red-400 hover:underline"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <Pagination total={total} limit={limit} skip={skip} onPageChange={(newSkip) => setSkip(newSkip)} />
    </div>
  );
};

export default Assignments;