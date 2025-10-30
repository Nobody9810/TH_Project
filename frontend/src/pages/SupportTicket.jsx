import React, { useCallback, useEffect, useMemo, useState } from "react";
import axiosClient from "../api/axiosClient";
import Header from '../components/Header'; // 导入统一的Header

// --- 常量/配置 ---
const CATEGORIES = [
  { value: "all", label: "全部问题", color: "from-gray-500 to-gray-600" },
  { value: "faq", label: "常见问题", color: "from-blue-500 to-blue-600" },
  { value: "ticket", label: "订票问题", color: "from-green-500 to-green-600" },
  { value: "car", label: "汽车问题", color: "from-orange-500 to-orange-600" },
  { value: "incident", label: "意外情况", color: "from-red-500 to-red-600" },
];

const STATUS_FILTERS = [
  { value: "all", label: "所有状态", color: "from-gray-500 to-gray-600" },
  { value: "answered", label: "已解决", color: "from-green-500 to-green-600" },
  { value: "unanswered", label: "待处理", color: "from-orange-500 to-orange-600" },
];

// 新建问题的类别选项（排除"all"）
const NEW_TICKET_CATEGORIES = CATEGORIES.filter(cat => cat.value !== 'all');

// --- 辅助组件/函数 ---
function SkeletonLoader() {
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 animate-pulse border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="h-6 bg-gray-200 rounded w-16"></div>
      </div>
      <div className="h-12 bg-gray-200 rounded-xl"></div>
    </div>
  );
}

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

const getCategoryLabel = (value) => {
  return CATEGORIES.find(c => c.value === value)?.label || '未知';
};

const getCategoryColor = (value) => {
  return CATEGORIES.find(c => c.value === value)?.color || 'from-gray-500 to-gray-600';
};

const LoadingSpinner = ({ size = "small" }) => {
  const sizeClasses = {
    small: "h-4 w-4",
    medium: "h-6 w-6",
    large: "h-8 w-8"
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}></div>
  );
};

// --- 主组件 ---
export default function SupportTicketManagement() {
  const [tickets, setTickets] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [error, setError] = useState(null);

  // 筛选状态
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // 回答相关状态
  const [answerContent, setAnswerContent] = useState("");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [answering, setAnswering] = useState(false);

  // 新建问题模态框状态
  const [showNewTicketModal, setShowNewTicketModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newTicket, setNewTicket] = useState({
    question_text: "",
    category: NEW_TICKET_CATEGORIES[0].value,
  });

  const isTicketSelected = !!selectedTicket;

  // 关闭详情侧栏
  const closeDetails = () => {
    setSelectedTicket(null);
    setAnswerContent("");
  };

  // 当选中问题变化时，初始化回答内容
  useEffect(() => {
    if (selectedTicket) {
      setAnswerContent(selectedTicket.answer_content || "");
    }
  }, [selectedTicket]);

  // --- 数据获取逻辑 ---
  const fetchTickets = useCallback(
    async (pageToLoad = 1, searchQuery = query, searchCategory = category, searchStatus = statusFilter) => {
      const isInitialLoad = pageToLoad === 1;
      const isPaging = pageToLoad > 1;

      if (isInitialLoad) setIsLoading(true);
      if (isPaging) setLoadingMore(true);

      setError(null);

      const params = {
        page: pageToLoad,
        page_size: pageSize,
      };


      // 添加筛选参数
      if (searchQuery.trim()) params.query = searchQuery.trim();
      if (searchCategory !== "all") params.category = searchCategory;
      if (searchStatus !== "all") params.status = searchStatus; // 这里发送 status 参数

      if (query.trim()) params.query = query.trim();
      if (category !== "all") params.category = category;
      if (statusFilter !== "all") params.status = statusFilter;

      try {
        const response = await axiosClient.get("supportticket/", { params });

        if (response.data && typeof response.data === 'object') {
          setTotalCount(response.data.count || 0);

          const newTickets = response.data.results || [];

          if (isPaging) {
            setTickets((prev) => [...(prev || []), ...newTickets]);
          } else {
            setTickets(newTickets);
          }
          setPage(pageToLoad);
        } else {
          setTickets([]);
          setTotalCount(0);
          setError("数据格式错误，请检查API响应。");
        }
      } catch (err) {
        console.error("获取问题列表失败:", err);
        setError("无法加载问题列表，请检查网络或权限。");
        setTickets([]);
        setTotalCount(0);
      } finally {
        setIsLoading(false);
        setLoadingMore(false);
      }
    },
    [pageSize, query, category, statusFilter]
  );

  // 筛选条件变化时重新加载
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTickets(1);
      closeDetails();
    }, 300); // 添加防抖，300ms延迟

    return () => clearTimeout(timer);
  }, [query, category, statusFilter]); // 监听搜索词和筛选条件的变化

  // 搜索处理
  const handleCategoryChange = (e) => {
    setCategory(e.target.value);
  };

  // 筛选器变更处理
  const handleStatusChange = (e) => {
    setStatusFilter(e.target.value);
  };

  const handleSearchChange = (e) => {
    setQuery(e.target.value);
  };

  // 提交回答
  const submitAnswer = useCallback(async () => {
    if (!selectedTicket || !answerContent.trim()) return;

    setAnswering(true);
    try {
      const updateData = {
        answer_content: answerContent.trim(),
      };

      const response = await axiosClient.patch(
        `supportticket/${selectedTicket.id}/`,
        updateData
      );

      const updatedTicket = response.data;
      setTickets((prev) =>
        (prev || []).map((ticket) =>
          ticket.id === updatedTicket.id ? updatedTicket : ticket
        )
      );
      setSelectedTicket(updatedTicket);

      // 使用更美观的成功提示
      setError(null);
    } catch (error) {
      console.error("保存解答失败:", error);
      setError("保存解答失败，请重试。");
    } finally {
      setAnswering(false);
    }
  }, [selectedTicket, answerContent]);

  // 新建问题处理函数
  const handleNewTicketChange = (e) => {
    const { name, value } = e.target;
    setNewTicket({ ...newTicket, [name]: value });
  };

  // 提交新问题
  const submitNewTicket = async () => {
    if (!newTicket.question_text.trim()) {
      alert("问题描述不能为空。");
      return;
    }

    setIsSubmitting(true);
    try {
      await axiosClient.post("supportticket/", {
        category: newTicket.category,
        question_text: newTicket.question_text,
      });

      alert("问题提交成功，管理员将尽快处理！");

      setNewTicket({
        question_text: "",
        category: NEW_TICKET_CATEGORIES[0].value,
      });
      setShowNewTicketModal(false);
      fetchTickets(1); // 刷新列表

    } catch (error) {
      console.error("提交问题失败:", error.response || error);
      alert(`提交失败: ${error.response?.data?.detail || "请检查权限或网络。"}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const showLoadMore = Array.isArray(tickets) && tickets.length > 0 &&
    !isLoading && !loadingMore &&
    tickets.length < totalCount;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/50 to-indigo-100/50">
      <div className="w-full">
        <Header />

        {/* 主内容区域 */}
        <div className="max-w-7xl mx-auto p-6">
          {/* 头部 */}
          <header className="mb-8 text-center">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
              知识资源库
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              浏览、筛选和搜索所有相关问题，获取帮助和支持
            </p>
          </header>

          {/* 筛选和搜索栏 */}
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-200">
            <div className="flex flex-col lg:flex-row items-center gap-4">
              {/* 关键词搜索 */}
              <div className="flex-1 w-full">
                <div className="relative">
                  <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <input
                    type="text"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
                    placeholder="搜索问题描述或回答内容..."
                    value={query}
                    onChange={handleSearchChange}
                  />
                </div>
              </div>

              {/* 分类筛选 */}
              <select
                value={category}
                onChange={handleCategoryChange}
                className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors w-full lg:w-auto"
              >
                {CATEGORIES.map(c => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>

              {/* 状态筛选 */}
              <select
                value={statusFilter}
                onChange={handleStatusChange}
                className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors w-full lg:w-auto"
              >
                {STATUS_FILTERS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>

              {/* 操作按钮 */}
              <div className="flex gap-3 w-full lg:w-auto">

                <button
                  onClick={() => setShowNewTicketModal(true)}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 flex items-center gap-2 justify-center"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  新建问题
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
          {!isLoading && tickets.length > 0 && (
            <div className="mb-6 text-sm text-gray-600">
              找到 <span className="font-semibold text-blue-600">{tickets.length}</span> 个问题
              {totalCount > tickets.length && `，共 ${totalCount} 个`}
            </div>
          )}

          {/* 问题列表 */}
          <div className="grid grid-cols-1 gap-4">
            {isLoading && page === 1 ? (
              Array.from({ length: 5 }).map((_, index) => <SkeletonLoader key={index} />)
            ) : Array.isArray(tickets) && tickets.length > 0 ? (
              tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  onClick={() => setSelectedTicket(ticket)}
                  className={`group bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-1 cursor-pointer border-2 ${selectedTicket?.id === ticket.id
                      ? 'border-blue-500 bg-blue-50/30'
                      : 'border-white hover:border-blue-200'
                    }`}
                >
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 text-lg line-clamp-2 pr-4 mb-2 group-hover:text-blue-600 transition-colors">
                          {ticket.question_text}
                        </h3>

                        <div className="flex items-center gap-3 flex-wrap">
                          <span className={`bg-gradient-to-r ${getCategoryColor(ticket.category)} text-white px-3 py-1 rounded-full text-xs font-semibold`}>
                            {ticket.category_display || getCategoryLabel(ticket.category)}
                          </span>
                          <span className={`text-xs font-semibold px-3 py-1 rounded-full ${ticket.is_answered
                              ? 'bg-gradient-to-r from-green-100 to-green-200 text-green-800'
                              : 'bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800'
                            }`}>
                            {ticket.is_answered ? '✅ 已解决' : '⏳ 待处理'}
                          </span>
                        </div>
                      </div>

                      <div className="flex-shrink-0 ml-4">
                        <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm text-gray-500 mt-4">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {ticket.author?.username || '用户'}
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {formatDate(ticket.created_at)}
                        </span>
                      </div>
                      <span className="text-xs bg-gray-100 px-2 py-1 rounded">#{ticket.id}</span>
                    </div>

                    {/* 回答预览 */}
                    {ticket.is_answered && ticket.answer_content && (
                      <div className="mt-4 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                        <div className="text-xs text-green-700 font-medium mb-1 flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          管理员回复
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {ticket.answer_content}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full bg-white p-12 rounded-2xl shadow-lg text-center border border-gray-200">
                <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-r from-gray-100 to-gray-200 rounded-full flex items-center justify-center">
                  <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">暂无问题数据</h3>
                <p className="text-gray-600">当前筛选条件下没有找到匹配的问题</p>
              </div>
            )}
          </div>

          {/* 加载更多 */}
          {showLoadMore && (
            <div className="text-center mt-8">
              <button
                onClick={() => fetchTickets(page + 1)}
                disabled={loadingMore}
                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:transform-none flex items-center gap-2 mx-auto"
              >
                {loadingMore ? (
                  <>
                    <LoadingSpinner size="small" />
                    加载中...
                  </>
                ) : (
                  `加载更多 (${tickets.length}/${totalCount})`
                )}
              </button>
            </div>
          )}
        </div>

        {/* 详情侧边栏 */}
        <div
          className={`fixed lg:relative top-0 right-0 h-full bg-white shadow-2xl z-40 transition-all duration-500 ease-in-out 
            ${isTicketSelected ? 'w-full lg:w-1/3 translate-x-0' : 'w-0 lg:w-0 translate-x-full'}`}
        >
        </div>
          {selectedTicket && (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity duration-300">
              <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden transform transition-all duration-300 scale-100">
                {/* 头部 */}
                <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900">问题详情与解答</h2>
                  <button
                    onClick={closeDetails}
                    className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-800"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                  </button>
                </div>

                {/* 内容区域 */}
                <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
                  {/* 问题信息 */}
                  <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                      <span className={`text-sm font-semibold px-3 py-1 rounded-full ${selectedTicket.is_answered
                          ? 'bg-gradient-to-r from-green-100 to-green-200 text-green-800'
                          : 'bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800'
                        }`}>
                        {selectedTicket.is_answered ? '✅ 已解决' : '⏳ 待处理'}
                      </span>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        #{selectedTicket.id}
                      </span>
                    </div>

                    <div className="space-y-3 mb-6">
                      <div className="flex items-center gap-2">
                        <span className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                          {selectedTicket.category_display || getCategoryLabel(selectedTicket.category)}
                        </span>
                      </div>

                      <h3 className="text-xl font-bold text-gray-900 leading-relaxed">
                        {selectedTicket.question_text}
                      </h3>

                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {selectedTicket.author?.username || '用户'}
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {formatDate(selectedTicket.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 回答区域 */}
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      {selectedTicket.is_answered ? '解决方案' : '问题处理'}
                    </h3>

                    {/* 现有回答展示 */}
                    {selectedTicket.is_answered && selectedTicket.answer_content ? (
                      <div className="mb-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200">
                        <div className="text-xs text-green-700 mb-3 flex items-center justify-between">
                          <span className="flex items-center gap-1 font-semibold">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                            解答人: {selectedTicket.answered_by?.username || '管理员'}
                          </span>
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {formatDate(selectedTicket.answered_at)}
                          </span>
                        </div>
                        <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {selectedTicket.answer_content}
                        </div>
                      </div>
                    ) : (
                      <div className="mb-6 p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl border border-orange-200 text-center">
                        <svg className="w-12 h-12 text-orange-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.464-.833-2.232 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <p className="text-orange-800 font-medium">此问题尚未处理</p>
                        <p className="text-orange-600 text-sm mt-1">请及时为用户提供解决方案</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        {/* 移动端遮罩层 */}
        {isTicketSelected && (
          <div
            onClick={closeDetails}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-30 transition-opacity duration-300 lg:hidden"
          ></div>
        )}
      </div>

      {/* 新建问题模态框 */}
      {showNewTicketModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity duration-300">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl transform transition-all duration-300 scale-100">
            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">新建支持问题</h3>
              <button
                onClick={() => !isSubmitting && setShowNewTicketModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
                disabled={isSubmitting}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">问题分类</label>
                <select
                  name="category"
                  value={newTicket.category}
                  onChange={handleNewTicketChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
                  disabled={isSubmitting}
                >
                  {NEW_TICKET_CATEGORIES.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">问题描述</label>
                <textarea
                  name="question_text"
                  value={newTicket.question_text}
                  onChange={handleNewTicketChange}
                  rows={6}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none transition-colors"
                  placeholder="请详细描述您遇到的问题或需求..."
                  disabled={isSubmitting}
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50/50 rounded-b-2xl flex justify-end gap-3">
              <button
                onClick={() => !isSubmitting && setShowNewTicketModal(false)}
                className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                disabled={isSubmitting}
              >
                取消
              </button>
              <button
                onClick={submitNewTicket}
                disabled={isSubmitting || !newTicket.question_text.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:shadow-lg transition-all duration-300 font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="small" />
                    提交中...
                  </>
                ) : (
                  "提交问题"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}