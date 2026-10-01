import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../api/client';
import AnimatedPage from '../components/AnimatedPage';
import { FiShare2 } from 'react-icons/fi';
import toast from 'react-hot-toast';

const ProfilePage: React.FC = () => {
  const { user, isTeacher, refreshUser } = useAuth();
  const [formData, setFormData] = useState({
    full_name: '',
    about: '',
    education: '',
    experience_years: 0,
    avatar: '',
  });
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        about: (user as any).about || '',
        education: (user as any).education || '',
        experience_years: (user as any).experience_years || 0,
        avatar: (user as any).avatar || '',
      });
    }
  }, [user]);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Файл слишком большой. Максимум 5 МБ');
      return;
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Можно загружать только JPEG, PNG, GIF или WEBP');
      return;
    }

    setUploading(true);
    const formDataFile = new FormData();
    formDataFile.append('file', file);

    try {
      const response = await apiClient.post('/upload', formDataFile, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const avatarUrl = response.data.url;
      setFormData((prev) => ({ ...prev, avatar: avatarUrl }));
      toast.success('Аватар загружен');
    } catch (error) {
      console.error('Error uploading avatar:', error);
      toast.error('Ошибка при загрузке аватара');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.put('/users/profile', formData);
      if (refreshUser) await refreshUser();
      toast.success('Профиль обновлён');
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Ошибка при обновлении');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <AnimatedPage>
      <div className="container mx-auto px-4 py-6 max-w-3xl">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-white">Редактирование профиля</h1>
          {isTeacher && (
            <button
              onClick={() => {
                const shareUrl = `${window.location.origin}/tutor/${user?.id}`;
                navigator.clipboard.writeText(shareUrl);
                toast.success('Ссылка на публичную карточку скопирована');
              }}
              className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition flex items-center gap-2 text-sm"
            >
              <FiShare2 size={16} />
              Поделиться карточкой
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Полное имя</label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Аватар</label>
            <div className="flex items-center gap-4 flex-wrap">
              {formData.avatar && (
                <img
                  src={formData.avatar}
                  alt="Avatar"
                  className="w-16 h-16 rounded-full object-cover bg-gray-700"
                />
              )}
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarUpload}
                disabled={uploading}
                className="flex-1 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white file:mr-2 file:py-1 file:px-3 file:rounded-lg file:bg-accent file:text-white file:border-0 cursor-pointer disabled:opacity-50"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Загрузите изображение (PNG, JPG, до 5 МБ)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">О себе</label>
            <textarea
              value={formData.about}
              onChange={(e) => setFormData({ ...formData, about: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
              placeholder="Расскажите о своём опыте, методике преподавания..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Образование</label>
            <textarea
              value={formData.education}
              onChange={(e) => setFormData({ ...formData, education: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
              placeholder="МГУ им. Ломоносова, физический факультет (2015)"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Опыт (лет)</label>
            <input
              type="number"
              value={formData.experience_years}
              onChange={(e) =>
                setFormData({ ...formData, experience_years: parseInt(e.target.value) || 0 })
              }
              className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading || uploading}
              className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/80 text-white font-medium disabled:opacity-50"
            >
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        </form>
      </div>
    </AnimatedPage>
  );
};

export default ProfilePage;