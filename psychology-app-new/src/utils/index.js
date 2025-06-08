// Format functions
export const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  // Validate functions
  export const validateIdCard = (idCard) => {
    // Simple validation for Chinese ID card (18 digits)
    const idCardRegex = /(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
    return idCardRegex.test(idCard);
  };
  
  export const validatePhone = (phone) => {
    // Simple validation for Chinese phone numbers
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
  };
  
  export const validateAge = (age) => {
    const parsedAge = parseInt(age, 10);
    return !isNaN(parsedAge) && parsedAge > 0 && parsedAge < 150;
  };
  
  // Local storage helpers
  export const saveToLocalStorage = (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('Error saving to localStorage:', error);
      return false;
    }
  };
  
  export const getFromLocalStorage = (key) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error getting from localStorage:', error);
      return null;
    }
  };
  
  // Default psychology tips for fallback
  export const defaultTips = [
    {
      category: '心理小贴士',
      title: '专注力提升',
      content: '每天花5分钟进行深呼吸冥想，可以有效提高注意力和减少分心。'
    },
    {
      category: '心理小贴士',
      title: '情绪管理',
      content: '感到焦虑时，尝试"5-4-3-2-1"技巧：说出5个你看到的东西，4个你触摸到的东西，3个你听到的声音，2个你闻到的气味，1个你尝到的味道。'
    },
    {
      category: '心理小贴士',
      title: '人际关系',
      content: '积极倾听是建立良好人际关系的关键，尝试在对话中花80%的时间倾听，20%的时间讲话。'
    },
    {
      category: '心理小贴士',
      title: '自我成长',
      content: '研究表明，学习新技能不仅能提高能力，还能增加幸福感和降低抑郁风险。'
    },
    {
      category: '心理小贴士',
      title: '压力缓解',
      content: '感到压力大时，尝试"方块呼吸法"：吸气4秒，屏息4秒，呼气4秒，再屏息4秒，构成一个完整的"方块"循环。'
    }
  ];
  
  // Get a random tip from the default tips array
  export const getRandomDefaultTip = () => {
    const randomIndex = Math.floor(Math.random() * defaultTips.length);
    return defaultTips[randomIndex];
  };