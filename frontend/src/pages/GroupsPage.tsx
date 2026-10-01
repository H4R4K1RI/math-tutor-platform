import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth } from '../context/AuthContext';
import AnimatedPage from '../components/AnimatedPage';
import { FiUsers, FiPlus, FiEdit2, FiTrash2, FiUserPlus, FiEye } from 'react-icons/fi';

interface Group {
  id: number;
  name: string;
  description: string | null;
  student_count: number;
  created_at: string;
}

interface Student {
  id: number;
  name: string;
  email: string;
}

const GroupsPage: React.FC = () => {
  const { isTeacher } = useAuth();
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [groupStudents, setGroupStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Модальные окна
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAddStudentModal, setShowAddStudentModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [selectedStudentIds, setSelectedStudentIds] = useState<number[]>([]);
  
  // Формы
  const [groupName, setGroupName] = useState('');
  const [groupDescription, setGroupDescription] = useState('');

  useEffect(() => {
    if (!isTeacher) return;
    fetchGroups();
    fetchStudents();
  }, [isTeacher]);

  const fetchGroups = async () => {
    try {
      const response = await apiClient.get('/groups');
      setGroups(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching groups:', error);
      setGroups([]);
    } finally {
      setLoading(false);
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
  const fetchGroupStudents = async (groupId: number) => {
    try {
      const response = await apiClient.get(`/groups/${groupId}/students`);
      setGroupStudents(response.data);
    } catch (error) {
      console.error('Error fetching group students:', error);
    }
  };

  const createGroup = async () => {
    if (!groupName.trim()) return;
    try {
      await apiClient.post('/groups', { name: groupName, description: groupDescription });
      setShowCreateModal(false);
      setGroupName('');
      setGroupDescription('');
      fetchGroups();
    } catch (error) {
      console.error('Error creating group:', error);
      alert('Ошибка при создании группы');
    }
  };

  const updateGroup = async () => {
    if (!selectedGroup || !groupName.trim()) return;
    try {
      await apiClient.put(`/groups/${selectedGroup.id}`, { 
        name: groupName, 
        description: groupDescription 
      });
      setShowEditModal(false);
      setSelectedGroup(null);
      setGroupName('');
      setGroupDescription('');
      fetchGroups();
    } catch (error) {
      console.error('Error updating group:', error);
      alert('Ошибка при обновлении группы');
    }
  };

  const deleteGroup = async (groupId: number) => {
    if (!confirm('Удалить группу? Ученики не будут удалены.')) return;
    try {
      await apiClient.delete(`/groups/${groupId}`);
      fetchGroups();
    } catch (error) {
      console.error('Error deleting group:', error);
      alert('Ошибка при удалении группы');
    }
  };

  const addStudentsToGroup = async () => {
    if (!selectedGroup || selectedStudentIds.length === 0) return;
    
    for (const studentId of selectedStudentIds) {
      try {
        await apiClient.post(`/groups/${selectedGroup.id}/students/${studentId}`);
      } catch (error) {
        console.error(`Error adding student ${studentId}:`, error);
      }
    }
    
    setShowAddStudentModal(false);
    setSelectedStudentIds([]);
    fetchGroups();
  };

  const toggleStudentSelection = (studentId: number) => {
    setSelectedStudentIds(prev =>
      prev.includes(studentId)
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  const openAddStudentModal = async (group: Group) => {
    setSelectedGroup(group);
    setSelectedStudentIds([]);
    await fetchGroupStudents(group.id);
    setShowAddStudentModal(true);
  };

  const openEditModal = (group: Group) => {
    setSelectedGroup(group);
    setGroupName(group.name);
    setGroupDescription(group.description || '');
    setShowEditModal(true);
  };

  const viewGroup = (groupId: number) => {
    navigate(`/groups/${groupId}`);
  };

  // Доступные ученики (не в группе)
  const availableStudents = students.filter(
    s => !groupStudents.some(gs => gs.id === s.id)
  );

  if (!isTeacher) {
    return <div className="text-center py-20 text-white">Доступ только для учителей</div>;
  }

  if (loading) {
    return (
      <div className="text-center py-20 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
        <p>Загрузка групп...</p>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-6xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Группы учеников</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
          >
            <FiPlus size={18} />
            <span>Создать группу</span>
          </button>
        </div>

        {groups.length === 0 ? (
          <div className="text-center py-20 text-gray-400">
            <FiUsers size={48} className="mx-auto mb-4 opacity-50" />
            <p>У вас пока нет групп</p>
            <p className="text-sm">Нажмите "Создать группу", чтобы объединить учеников</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groups.map((group) => (
              <div
                key={group.id}
                className="bg-dark-card rounded-xl p-5 border border-white/10 hover:shadow-lg transition-all duration-200"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-semibold text-white text-lg">{group.name}</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openEditModal(group)}
                      className="text-gray-400 hover:text-accent transition"
                      title="Редактировать"
                    >
                      <FiEdit2 size={16} />
                    </button>
                    <button
                      onClick={() => deleteGroup(group.id)}
                      className="text-gray-400 hover:text-red-400 transition"
                      title="Удалить"
                    >
                      <FiTrash2 size={16} />
                    </button>
                  </div>
                </div>
                {group.description && (
                  <p className="text-gray-400 text-sm mb-3">{group.description}</p>
                )}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <FiUsers size={14} />
                    <span>{group.student_count} учеников</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => viewGroup(group.id)}
                      className="text-accent hover:text-accent/80 transition flex items-center gap-1 text-sm"
                      title="Просмотреть группу"
                    >
                      <FiEye size={14} />
                      <span>Просмотр</span>
                    </button>
                    <button
                      onClick={() => openAddStudentModal(group)}
                      className="text-accent hover:text-accent/80 transition flex items-center gap-1 text-sm"
                      title="Добавить учеников"
                    >
                      <FiUserPlus size={14} />
                      <span>Добавить</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Модальное окно создания группы (без изменений) */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Создать группу</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Название группы</label>
                  <input
                    type="text"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Например: 9А класс"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Описание (необязательно)</label>
                  <textarea
                    value={groupDescription}
                    onChange={(e) => setGroupDescription(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    rows={3}
                    placeholder="Например: Подготовка к ОГЭ"
                  />
                </div>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={createGroup}
                    disabled={!groupName.trim()}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    Создать
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно редактирования группы (без изменений) */}
        {showEditModal && selectedGroup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">Редактировать группу</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Название группы</label>
                  <input
                    type="text"
                    value={groupName}
                    onChange={(e) => setGroupName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Описание</label>
                  <textarea
                    value={groupDescription}
                    onChange={(e) => setGroupDescription(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    rows={3}
                  />
                </div>
                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={updateGroup}
                    disabled={!groupName.trim()}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                  >
                    Сохранить
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно добавления учеников (с чекбоксами) */}
        {showAddStudentModal && selectedGroup && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <h2 className="text-xl font-semibold text-white mb-4">
                Добавить учеников в "{selectedGroup.name}"
              </h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {availableStudents.length === 0 ? (
                  <p className="text-gray-400 text-center py-4">Нет доступных учеников</p>
                ) : (
                  availableStudents.map((student) => (
                    <label
                      key={student.id}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition ${
                        selectedStudentIds.includes(student.id)
                          ? 'bg-accent/20 border border-accent'
                          : 'bg-gray-800 hover:bg-gray-700'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedStudentIds.includes(student.id)}
                        onChange={() => toggleStudentSelection(student.id)}
                        className="w-4 h-4 rounded border-gray-600 text-accent focus:ring-accent"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-white">{student.name}</p>
                        <p className="text-sm text-gray-400">{student.email}</p>
                      </div>
                    </label>
                  ))
                )}
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowAddStudentModal(false)}
                  className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10 transition"
                >
                  Отмена
                </button>
                <button
                  onClick={addStudentsToGroup}
                  disabled={selectedStudentIds.length === 0}
                  className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition disabled:opacity-50"
                >
                  Добавить ({selectedStudentIds.length})
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default GroupsPage;