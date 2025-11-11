import Header from '../components/Header'; // 导入统一的Header

import React, { useEffect, useState, useCallback } from "react";
import axiosClient from "../api/axiosClient";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Pagination, Autoplay } from "swiper/modules";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/pagination";


const DJANGO_API_ROOT = "https://api.trippalholiday.my/api";
const getImageUrl = (url) => {
  if (!url) return '';
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}t=${Date.now()}`;
};


// --- 子组件：骨架加载卡片 ---
const SkeletonCard = () => (
  <div className="bg-white rounded-2xl shadow-lg p-6 animate-pulse">
    <div className="h-48 w-full bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl mb-4" />
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
    <div className="h-3 bg-gray-200 rounded w-1/2 mb-3" />
    <div className="h-3 bg-gray-200 rounded w-1/4 mb-4" />
    <div className="flex gap-2">
      <div className="h-10 bg-gray-200 rounded-lg flex-1" />
      <div className="h-10 bg-gray-200 rounded-lg flex-1" />
    </div>
  </div>
);

// --- 子组件：素材卡片 ---
const MaterialCard = ({ material, onSelect }) => {
  const typeStyles = {
    hotel: {
      bg: "bg-gradient-to-r from-blue-500 to-blue-600",
      text: "text-white",
      badge: "from-blue-100 to-blue-200 text-blue-800"
    },
    ticket: {
      bg: "bg-gradient-to-r from-green-500 to-green-600",
      text: "text-white",
      badge: "from-green-100 to-green-200 text-green-800"
    },
    route: {
      bg: "bg-gradient-to-r from-purple-500 to-purple-600",
      text: "text-white",
      badge: "from-purple-100 to-purple-200 text-purple-800"
    },
    transport: {
      bg: "bg-gradient-to-r from-yellow-500 to-orange-500",
      text: "text-white",
      badge: "from-yellow-100 to-orange-200 text-orange-800"
    },
  };
  const style = typeStyles[material.material_type] || {};

  return (
    <div className="group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 flex flex-col overflow-hidden border border-gray-100">
      {/* 图片区域 */}
      <div className="h-48 w-full relative overflow-hidden">
        <img
          src={getImageUrl(material.header_image) || "https://via.placeholder.com/400x300.png?text=No+Image"}
          alt={material.title}
          className="h-full w-full object-cover group-hover:scale-110 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
        <span className={`absolute top-3 right-3 px-3 py-1 text-xs font-semibold rounded-full bg-gradient-to-r ${style.badge} backdrop-blur-sm`}>
          {material.material_type_display}
        </span>
      </div>

      {/* 内容区域 */}
      <div className="p-6 flex-grow flex flex-col">
        <p className="text-sm text-gray-500 mb-2 flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {material.destination?.name || "通用"}
        </p>

        <h2 className="text-xl font-bold text-gray-900 flex-grow line-clamp-2 mb-3 group-hover:text-blue-600 transition-colors">
          {material.title}
        </h2>

        {material.price && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              RM {Number(material.price).toFixed(2)}
            </span>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="mt-auto pt-4 border-t border-gray-100 flex items-center gap-3">
          <button
            onClick={() => onSelect(material)}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            查看详情
          </button>
          <a
            href={`${DJANGO_API_ROOT}/materials/${material.id}/download-pdf/`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 px-4 py-3 bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2  text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            下载PDF
          </a>
        </div>
      </div>
    </div>
  );
};

// --- 子组件：详情弹窗 ---
const MaterialDetailModal = ({ material, onClose }) => {
  if (!material) return null;

  // 获取视频文件的完整URL
  const getVideoUrl = (videoPath) => {
    if (!videoPath) return null;
    // 如果视频路径已经是完整URL，直接返回
    if (videoPath.startsWith('http')) return videoPath;
    // 否则拼接完整的URL
    return `${DJANGO_API_ROOT.replace('/api', '')}${videoPath}`;
  };

  const videoUrl = getVideoUrl(material.video);


  const fixedDescription = material.description
    ? material.description.replaceAll(
      '/media/',
      `${DJANGO_API_ROOT.replace('/api', '')}/media/`
    )
    : "暂无描述";


  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 transition-opacity duration-300"
      onClick={onClose}
    >
      <div
        className="max-w-4xl w-full bg-white rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-300 scale-100 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white sticky top-0 z-10">
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{material.title}</h3>
            <p className="text-sm text-gray-600 mt-1">
              {material.destination?.name || "通用"} • {material.material_type_display}
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-800"
            aria-label="关闭"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6">
          {material.videos?.length > 0 && (
            <div className="mb-8">
              <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                视频库 ({material.videos.length} 个视频)
              </h4>
              <Swiper
                modules={[Navigation, Pagination]}
                spaceBetween={20}
                slidesPerView={1}
                navigation
                pagination={{ clickable: true }}
                className="rounded-2xl shadow-lg"
              >
                {material.videos.map((vid) => (
                  <SwiperSlide key={vid.id}>
                    <div className="bg-black rounded-2xl overflow-hidden">
                      <video
                        controls
                        className="w-full h-auto max-h-96 object-contain"
                        poster={vid.thumbnail ? getImageUrl(vid.thumbnail) : getImageUrl(material.header_image)}
                      >
                        <source src={getVideoUrl(vid.video)} type="video/mp4" />
                        您的浏览器不支持视频播放。
                      </video>
                      {vid.title && (
                        <div className="p-3 bg-gray-900 text-white">
                          <p className="font-semibold">{vid.title}</p>
                          {vid.description && <p className="text-sm text-gray-300 mt-1">{vid.description}</p>}
                        </div>
                      )}
                    </div>
                  </SwiperSlide>
                ))}
              </Swiper>
            </div>
          )}

          {/* 图片库 - 仅酒店类型显示 */}

          {material.images?.length > 0 && (
            <div className="mb-8">
              <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                图片库 ({material.images.length} 张图片)
              </h4>
              <Swiper
                modules={[Navigation, Pagination, Autoplay]}
                spaceBetween={20}
                slidesPerView={1}
                navigation
                pagination={{ clickable: true }}
                autoplay={{ delay: 3000, disableOnInteraction: false }}
                className="rounded-2xl shadow-lg"
              >
                {material.images.map((img) => (
                  <SwiperSlide key={img.id}>
                    <img
                      src={getImageUrl(img.image)}
                      alt={img.description || "素材图片"}
                      className="rounded-2xl object-cover w-full max-h-[400px] cursor-pointer"
                      loading="lazy"
                    />
                    {img.description && (
                      <div className="mt-2 text-center text-sm text-gray-600">
                        {img.description}
                      </div>
                    )}
                  </SwiperSlide>
                ))}
              </Swiper>
            </div>
          )}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 基本信息 */}
            <div className="lg:col-span-1">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  基本信息
                </h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 font-medium">类型:</span>
                    <span className="text-gray-900 font-semibold">{material.material_type_display}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-blue-100">
                    <span className="text-gray-600 font-medium">目的地:</span>
                    <span className="text-gray-900 font-semibold">{material.destination?.name || "—"}</span>
                  </div>
                  {material.price && (
                    <div className="flex justify-between items-center py-2 border-b border-blue-100">
                      <span className="text-gray-600 font-medium">价格:</span>
                      <span className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                        RM {Number(material.price).toFixed(2)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center py-2">
                    <span className="text-gray-600 font-medium">创建时间:</span>
                    <span className="text-gray-900 font-semibold">{new Date(material.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 详细描述 */}
            <div className="lg:col-span-2">
              <div className="bg-white border border-gray-200 rounded-2xl p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  详细描述
                </h4>
                {/* <div
                  className="prose prose-gray max-w-none"
                  dangerouslySetInnerHTML={{ __html: material.description || "暂无描述" }}
                /> */}


                <div
                  className="prose prose-gray max-w-none"
                  dangerouslySetInnerHTML={{ __html: fixedDescription }}
                />

              </div>
            </div>
          </div>
        </div>

        {/* 底部操作 */}
        <div className="p-6 bg-gradient-to-r from-gray-50 to-white border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            关闭
          </button>
          <a
            href={`${DJANGO_API_ROOT}/materials/${material.id}/download-pdf/`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            下载PDF
          </a>
        </div>
      </div>
    </div>
  );
};

// --- 主组件 ---
export default function Materials() {
  const [materials, setMaterials] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  // 筛选状态
  const [query, setQuery] = useState("");
  const [selectedType, setSelectedType] = useState("all");
  const [selectedDestination, setSelectedDestination] = useState("all");

  const [refreshTimestamp, setRefreshTimestamp] = useState(Date.now());

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (query) params.append('search', query);
    if (selectedType !== 'all') params.append('material_type', selectedType);
    if (selectedDestination !== 'all') params.append('destination__slug', selectedDestination);

    params.append('_t', Date.now());

    const fetchMaterials = axiosClient.get(`materials/?${params.toString()}`);
    const fetchDestinations = axiosClient.get("destinations/");

    Promise.all([fetchMaterials, fetchDestinations])
      .then(([materialsRes, destinationsRes]) => {
        setMaterials(materialsRes.data.results || materialsRes.data || []);
        setDestinations(destinationsRes.data.results || destinationsRes.data || []);
      })
      .catch((err) => {
        console.error(err);
        setError("无法加载素材库，请稍后重试。");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [query, selectedType, selectedDestination, refreshTimestamp]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleResetFilters = () => {
    setQuery("");
    setSelectedType("all");
    setSelectedDestination("all");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/50 to-indigo-100/50">
      {/* 使用统一的Header */}
      <Header
      />
      <div className="max-w-7xl mx-auto p-6">
        {/* 头部 */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
            素材资源库
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            浏览、筛选和下载所有可用的旅游素材资源
          </p>
        </header>

        {/* 筛选区域 */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-200">
          <div className="flex flex-col lg:flex-row items-center gap-4">
            {/* 搜索框 */}
            <div className="flex-1 w-full">
              <div className="relative">
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索标题、描述或目的地..."
                  className="pl-10 pr-4 py-3 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full transition-colors"
                />
              </div>
            </div>

            {/* 筛选器 */}
            <div className="flex flex-col sm:flex-row gap-3 w-full lg:w-auto">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-4 py-3 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="all">所有类型</option>
                <option value="hotel">酒店</option>
                <option value="ticket">景点门票</option>
                <option value="route">路线规划</option>
                <option value="transport">交通工具</option>
              </select>

              <select
                value={selectedDestination}
                onChange={(e) => setSelectedDestination(e.target.value)}
                className="px-4 py-3 text-sm border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="all">所有目的地</option>
                {destinations.map(d => (
                  <option key={d.id} value={d.slug}>{d.name}</option>
                ))}
              </select>

              <button
                onClick={handleResetFilters}
                className="px-6 py-3 bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-xl font-semibold hover:shadow-lg transition-all flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                重置筛选
              </button>
            </div>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-center gap-3">
            <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {error}
          </div>
        )}

        {/* 统计信息 */}
        {!loading && materials.length > 0 && (
          <div className="mb-6 text-sm text-gray-600">
            找到 <span className="font-semibold text-blue-600">{materials.length}</span> 个素材
          </div>
        )}

        {/* 内容网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {loading
            ? Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)
            : materials.length === 0
              ? (
                <div className="col-span-full bg-white p-12 rounded-2xl shadow-lg text-center border border-gray-200">
                  <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-r from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">未找到匹配的素材</h3>
                  <p className="text-gray-600 mb-4">请尝试调整您的筛选条件或搜索关键词</p>
                  <button
                    onClick={handleResetFilters}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    重置所有筛选
                  </button>
                </div>
              )
              : materials.map((material) => (
                <MaterialCard key={material.id} material={material} onSelect={setSelected} />
              ))}
        </div>

        {/* 详情弹窗 */}
        <MaterialDetailModal material={selected} onClose={() => setSelected(null)} />
      </div>
    </div>
  );
}
