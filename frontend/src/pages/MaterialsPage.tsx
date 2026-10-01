import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import {
  FiFolder,
  FiFolderPlus,
  FiFile,
  FiLink,
  FiVideo,
  FiPlus,
  FiEdit2,
  FiTrash2,
  FiUsers,
  FiX,
  FiEye,
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import { socket } from '../socket';

interface Folder {
  id: number;
  name: string;
  description: string | null;
  materials_count: number;
  created_at: string;
}

interface Material {
  id: number;
  folder_id: number;
  title: string;
  description: string | null;
  type: 'file' | 'link' | 'video';
  url: string | null;
  file_name: string | null;
  file_size: number | null;
  order: number;
}

interface Student {
  id: number;
  name: string;
  email: string;
}

const MaterialsPage: React.FC = () => {
  const { user, isTeacher } = useAuth();
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<Folder | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);

  const [showFolderModal, setShowFolderModal] = useState(false);
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [editingFolder, setEditingFolder] = useState<Folder | null>(null);
  const [editingMaterial, setEditingMaterial] = useState<Material | null>(null);
  const [accessStudents, setAccessStudents] = useState<number[]>([]);

  const [folderName, setFolderName] = useState('');
  const [folderDescription, setFolderDescription] = useState('');

  const [materialTitle, setMaterialTitle] = useState('');
  const [materialDescription, setMaterialDescription] = useState('');
  const [materialType, setMaterialType] = useState<'file' | 'link' | 'video'>('file');
  const [materialUrl, setMaterialUrl] = useState('');
  const [uploadedFile, setUploadedFile] = useState<{
    url: string;
    name: string;
    size: number;
  } | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchFolders();
    if (isTeacher) fetchStudents();
  }, []);

  useEffect(() => {
  if (!socket) return;

  const handleMaterialsUpdate = () => {
    fetchFolders();
    if (selectedFolder) {
      fetchMaterials(selectedFolder.id);
    }
  };

  socket.on('materials_updated', handleMaterialsUpdate);

  return () => {
    if (socket){socket.off('materials_updated', handleMaterialsUpdate);}
  };
}, [selectedFolder]);

  const fetchFolders = async () => {
    try {
      const response = await apiClient.get('/materials/folders');
      const data = Array.isArray(response.data) ? response.data : [];
      setFolders(data);
    } catch (error) {
      console.error('Error fetching folders:', error);
      setFolders([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMaterials = async (folderId: number) => {
    try {
      const response = await apiClient.get(`/materials/folders/${folderId}/items`);
      const data = Array.isArray(response.data) ? response.data : [];
      setMaterials(data);
    } catch (error) {
      console.error('Error fetching materials:', error);
      setMaterials([]);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/students');
      const data = response.data.items || response.data;
      setStudents(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching students:', error);
      setStudents([]);
    }
  };

  const fetchFolderAccess = async (folderId: number) => {
    try {
      const response = await apiClient.get(`/materials/folders/${folderId}/access`);
      const data = Array.isArray(response.data) ? response.data : [];
      setAccessStudents(data.map((s: Student) => s.id));
    } catch (error) {
      console.error('Error fetching access:', error);
      setAccessStudents([]);
    }
  };

  const handleCreateFolder = async () => {
    if (!folderName.trim()) {
      toast.error('Введите название папки');
      return;
    }

    try {
      if (editingFolder) {
        await apiClient.put(`/materials/folders/${editingFolder.id}`, {
          name: folderName,
          description: folderDescription,
        });
        toast.success('Папка обновлена');
      } else {
        await apiClient.post('/materials/folders', {
          name: folderName,
          description: folderDescription,
        });
        toast.success('Папка создана');
      }
      setShowFolderModal(false);
      setFolderName('');
      setFolderDescription('');
      setEditingFolder(null);
      fetchFolders();
    } catch (error) {
      console.error('Error saving folder:', error);
      toast.error('Ошибка при сохранении');
    }
  };

  const handleDeleteFolder = async (folderId: number) => {
    if (!confirm('Удалить папку со всеми материалами?')) return;
    try {
      await apiClient.delete(`/materials/folders/${folderId}`);
      toast.success('Папка удалена');
      if (selectedFolder?.id === folderId) {
        setSelectedFolder(null);
        setMaterials([]);
      }
      fetchFolders();
    } catch (error) {
      console.error('Error deleting folder:', error);
      toast.error('Ошибка при удалении');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      toast.error('Файл слишком большой. Максимум 50 МБ');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/materials/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadedFile({
        url: response.data.url,
        name: response.data.file_name,
        size: response.data.file_size,
      });
      toast.success('Файл загружен');
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error('Ошибка при загрузке файла');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateMaterial = async () => {
    if (!materialTitle.trim()) {
      toast.error('Введите название материала');
      return;
    }

    if (!selectedFolder) return;

    let url = '';
    let fileName = null;
    let fileSize = null;

    if (materialType === 'file') {
      if (!uploadedFile) {
        toast.error('Загрузите файл');
        return;
      }
      url = uploadedFile.url;
      fileName = uploadedFile.name;
      fileSize = uploadedFile.size;
    } else if (materialType === 'link' || materialType === 'video') {
      if (!materialUrl.trim()) {
        toast.error('Введите ссылку');
        return;
      }
      url = materialUrl;
    }

    try {
      if (editingMaterial) {
        await apiClient.put(`/materials/items/${editingMaterial.id}`, {
          title: materialTitle,
          description: materialDescription,
          order: 0,
        });
        toast.success('Материал обновлён');
      } else {
        await apiClient.post('/materials/items', {
          folder_id: selectedFolder.id,
          title: materialTitle,
          description: materialDescription,
          type: materialType,
          url: url,
          file_name: fileName,
          file_size: fileSize,
          order: materials.length,
        });
        toast.success('Материал добавлен');
      }
      setShowMaterialModal(false);
      setMaterialTitle('');
      setMaterialDescription('');
      setMaterialType('file');
      setMaterialUrl('');
      setUploadedFile(null);
      setEditingMaterial(null);
      if (selectedFolder) {
        fetchMaterials(selectedFolder.id);
      }
    } catch (error) {
      console.error('Error saving material:', error);
      toast.error('Ошибка при сохранении');
    }
  };

  const handleDeleteMaterial = async (materialId: number) => {
    if (!confirm('Удалить материал?')) return;
    try {
      await apiClient.delete(`/materials/items/${materialId}`);
      toast.success('Материал удалён');
      if (selectedFolder) {
        fetchMaterials(selectedFolder.id);
      }
    } catch (error) {
      console.error('Error deleting material:', error);
      toast.error('Ошибка при удалении');
    }
  };

  const handleSaveAccess = async () => {
    if (!selectedFolder) return;
    try {
      await apiClient.post(`/materials/folders/${selectedFolder.id}/access`, {
        student_ids: accessStudents,
      });
      toast.success('Доступ настроен');
      setShowAccessModal(false);
    } catch (error) {
      console.error('Error saving access:', error);
      toast.error('Ошибка при сохранении доступа');
    }
  };

  const openFolder = (folder: Folder) => {
    setSelectedFolder(folder);
    fetchMaterials(folder.id);
  };

  const openAccessModal = async (folder: Folder) => {
    setSelectedFolder(folder);
    setAccessStudents([]);
    await fetchFolderAccess(folder.id);
    setShowAccessModal(true);
  };

  const openEditFolder = (folder: Folder) => {
    setEditingFolder(folder);
    setFolderName(folder.name);
    setFolderDescription(folder.description || '');
    setShowFolderModal(true);
  };

  const openEditMaterial = (material: Material) => {
    setEditingMaterial(material);
    setMaterialTitle(material.title);
    setMaterialDescription(material.description || '');
    setMaterialType(material.type);
    if (material.type === 'file') {
      setUploadedFile({
        url: material.url || '',
        name: material.file_name || '',
        size: material.file_size || 0,
      });
    } else {
      setMaterialUrl(material.url || '');
    }
    setShowMaterialModal(true);
  };

  const getMaterialIcon = (type: string) => {
    switch (type) {
      case 'file':
        return <FiFile className="text-blue-400" />;
      case 'link':
        return <FiLink className="text-green-400" />;
      case 'video':
        return <FiVideo className="text-red-400" />;
      default:
        return <FiFile />;
    }
  };

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
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Библиотека материалов</h1>
          {isTeacher && (
            <button
              onClick={() => {
                setEditingFolder(null);
                setFolderName('');
                setFolderDescription('');
                setShowFolderModal(true);
              }}
              className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-2"
            >
              <FiFolderPlus size={18} />
              <span>Создать папку</span>
            </button>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Список папок */}
          <div className="bg-dark-card rounded-xl border border-white/10 overflow-hidden">
            <div className="p-4 border-b border-white/10">
              <h2 className="text-lg font-semibold text-white">Папки</h2>
            </div>
            <div className="divide-y divide-white/10 max-h-[600px] overflow-y-auto">
              {folders.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  <FiFolder size={48} className="mx-auto mb-2 opacity-50" />
                  <p>Нет папок</p>
                </div>
              ) : (
                folders.map((folder) => (
                  <div
                    key={folder.id}
                    className={`p-4 hover:bg-white/5 transition cursor-pointer ${
                      selectedFolder?.id === folder.id ? 'bg-accent/20' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1" onClick={() => openFolder(folder)}>
                        <div className="flex items-center gap-2">
                          <FiFolder className="text-accent" />
                          <span className="font-medium text-white">{folder.name}</span>
                          <span className="text-xs text-gray-500">
                            ({folder.materials_count})
                          </span>
                        </div>
                        {folder.description && (
                          <p className="text-gray-400 text-sm mt-1 line-clamp-1">
                            {folder.description}
                          </p>
                        )}
                      </div>
                      {isTeacher && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => openAccessModal(folder)}
                            className="p-1 text-gray-400 hover:text-accent transition"
                            title="Настроить доступ"
                          >
                            <FiUsers size={14} />
                          </button>
                          <button
                            onClick={() => openEditFolder(folder)}
                            className="p-1 text-gray-400 hover:text-accent transition"
                          >
                            <FiEdit2 size={14} />
                          </button>
                          <button
                            onClick={() => handleDeleteFolder(folder.id)}
                            className="p-1 text-gray-400 hover:text-red-400 transition"
                          >
                            <FiTrash2 size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Материалы выбранной папки */}
          <div className="lg:col-span-2 bg-dark-card rounded-xl border border-white/10 overflow-hidden">
            {!selectedFolder ? (
              <div className="p-12 text-center text-gray-400">
                <FiFolder size={64} className="mx-auto mb-4 opacity-50" />
                <p>Выберите папку слева</p>
              </div>
            ) : (
              <>
                <div className="p-4 border-b border-white/10 flex justify-between items-center flex-wrap gap-2">
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      {selectedFolder.name}
                    </h2>
                    {selectedFolder.description && (
                      <p className="text-gray-400 text-sm">
                        {selectedFolder.description}
                      </p>
                    )}
                  </div>
                  {isTeacher && (
                    <button
                      onClick={() => {
                        setEditingMaterial(null);
                        setMaterialTitle('');
                        setMaterialDescription('');
                        setMaterialType('file');
                        setMaterialUrl('');
                        setUploadedFile(null);
                        setShowMaterialModal(true);
                      }}
                      className="px-3 py-1 rounded-lg bg-accent hover:bg-accent/80 text-white transition flex items-center gap-1 text-sm"
                    >
                      <FiPlus size={14} />
                      <span>Добавить материал</span>
                    </button>
                  )}
                </div>
                <div className="divide-y divide-white/10 max-h-[600px] overflow-y-auto">
                  {materials.length === 0 ? (
                    <div className="p-8 text-center text-gray-400">
                      <p>В этой папке пока нет материалов</p>
                    </div>
                  ) : (
                    materials.map((material) => (
                      <div key={material.id} className="p-4 hover:bg-white/5 transition">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {getMaterialIcon(material.type)}
                              <span className="font-medium text-white">
                                {material.title}
                              </span>
                            </div>
                            {material.description && (
                              <p className="text-gray-400 text-sm mt-1">
                                {material.description}
                              </p>
                            )}
                            {material.type === 'file' && material.url && (
                              <a
                                href={material.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-accent text-sm hover:underline inline-flex items-center gap-1 mt-1"
                              >
                                <FiEye size={12} />
                                {material.file_name || 'Открыть файл'}
                              </a>
                            )}
                            {(material.type === 'link' || material.type === 'video') &&
                              material.url && (
                                <a
                                  href={material.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-accent text-sm hover:underline inline-flex items-center gap-1 mt-1"
                                >
                                  <FiLink size={12} />
                                  Открыть ссылку
                                </a>
                              )}
                          </div>
                          {isTeacher && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => openEditMaterial(material)}
                                className="p-1 text-gray-400 hover:text-accent transition"
                              >
                                <FiEdit2 size={14} />
                              </button>
                              <button
                                onClick={() => handleDeleteMaterial(material.id)}
                                className="p-1 text-gray-400 hover:text-red-400 transition"
                              >
                                <FiTrash2 size={14} />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Модальное окно создания/редактирования папки */}
        {showFolderModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  {editingFolder ? 'Редактировать папку' : 'Создать папку'}
                </h2>
                <button
                  onClick={() => setShowFolderModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <FiX size={20} />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Название
                  </label>
                  <input
                    type="text"
                    value={folderName}
                    onChange={(e) => setFolderName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Алгебра, Геометрия, Физика..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Описание
                  </label>
                  <textarea
                    value={folderDescription}
                    onChange={(e) => setFolderDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    placeholder="Описание папки..."
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowFolderModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleCreateFolder}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white"
                  >
                    {editingFolder ? 'Сохранить' : 'Создать'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно добавления материала */}
        {showMaterialModal && selectedFolder && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  {editingMaterial ? 'Редактировать материал' : 'Добавить материал'}
                </h2>
                <button
                  onClick={() => setShowMaterialModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <FiX size={20} />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Название *
                  </label>
                  <input
                    type="text"
                    value={materialTitle}
                    onChange={(e) => setMaterialTitle(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Тип материала
                  </label>
                  <select
                    value={materialType}
                    onChange={(e) =>
                      setMaterialType(e.target.value as 'file' | 'link' | 'video')
                    }
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                    disabled={!!editingMaterial}
                  >
                    <option value="file">Файл (PDF, изображение, видео)</option>
                    <option value="link">Ссылка (веб-страница)</option>
                    <option value="video">Видео (YouTube, Vimeo)</option>
                  </select>
                </div>

                {materialType === 'file' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Файл
                    </label>
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white file:mr-2 file:py-1 file:px-3 file:rounded-lg file:bg-accent file:text-white file:border-0"
                    />
                    {uploadedFile && (
                      <p className="text-green-400 text-sm mt-1">✅ {uploadedFile.name}</p>
                    )}
                  </div>
                )}

                {(materialType === 'link' || materialType === 'video') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Ссылка *
                    </label>
                    <input
                      type="url"
                      value={materialUrl}
                      onChange={(e) => setMaterialUrl(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                      placeholder="https://..."
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Описание
                  </label>
                  <textarea
                    value={materialDescription}
                    onChange={(e) => setMaterialDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
                  />
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowMaterialModal(false)}
                    className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={handleCreateMaterial}
                    disabled={uploading}
                    className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white disabled:opacity-50"
                  >
                    {editingMaterial ? 'Сохранить' : 'Добавить'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно настройки доступа */}
        {showAccessModal && selectedFolder && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-dark-card rounded-xl p-6 max-w-md w-full border border-white/10">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-white">
                  Доступ к папке "{selectedFolder.name}"
                </h2>
                <button
                  onClick={() => setShowAccessModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  <FiX size={20} />
                </button>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                <p className="text-gray-400 text-sm mb-2">
                  Выберите учеников, которые будут видеть эту папку
                </p>
                {students.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">Нет учеников</p>
                ) : (
                  students.map((student) => (
                    <label
                      key={student.id}
                      className="flex items-center gap-3 p-2 rounded-lg bg-gray-800 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={accessStudents.includes(student.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setAccessStudents([...accessStudents, student.id]);
                          } else {
                            setAccessStudents(
                              accessStudents.filter((id) => id !== student.id)
                            );
                          }
                        }}
                        className="w-4 h-4 rounded border-gray-600 text-accent"
                      />
                      <div>
                        <p className="text-white">{student.name}</p>
                        <p className="text-gray-400 text-sm">{student.email}</p>
                      </div>
                    </label>
                  ))
                )}
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowAccessModal(false)}
                  className="px-4 py-2 rounded-lg border border-white/20 text-gray-300 hover:bg-white/10"
                >
                  Отмена
                </button>
                <button
                  onClick={handleSaveAccess}
                  className="px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white"
                >
                  Сохранить
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AnimatedPage>
  );
};

export default MaterialsPage;