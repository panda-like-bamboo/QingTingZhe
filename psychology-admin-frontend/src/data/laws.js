// 文件路径: psychology-admin-frontend/src/data/laws.js

// 国家法律法规数据库基础搜索URL
const BASE_SEARCH_URL = 'https://flk.npc.gov.cn/search.html';

/**
 * 生成特定法律的搜索链接。
 * @param {string} lawName - 法律的全名。
 * @returns {string} - 指向官方数据库搜索结果页面的URL。
 */
function createSearchLink(lawName) {
  // 对法律名称进行URL编码，以处理特殊字符
  const encodedName = encodeURIComponent(lawName);
  // 构建搜索链接，keywordType=1 表示按标题搜索
  return `${BASE_SEARCH_URL}?keyword=${encodedName}&keywordType=1`;
}

// 导出的法律法规列表
export const laws = [
  {
    id: 1,
    name: '中华人民共和国刑法',
    description: '规定犯罪、刑事责任和刑罚的法律。',
    // 直接链接到搜索结果页，通常第一个就是目标法律
    link: createSearchLink('中华人民共和国刑法'),
  },
  {
    id: 2,
    name: '中华人民共和国治安管理处罚法',
    description: '关于维护社会治安秩序，保障公共安全的法律。',
    link: createSearchLink('中华人民共和国治安管理处罚法'),
  },
  {
    id: 3,
    name: '中华人民共和国消防法',
    description: '预防火灾和减少火灾危害，加强应急救援工作的法律。',
    link: createSearchLink('中华人民共和国消防法'),
  },
  {
    id: 4,
    name: '中华人民共和国禁毒法',
    description: '预防和惩治毒品违法犯罪行为，保护公民身心健康的法律。',
    link: createSearchLink('中华人民共和国禁毒法'),
  },
  {
    id: 5,
    name: '公安机关办理刑事案件程序规定',
    description: '公安机关办理刑事案件时应当遵守的具体程序规则。',
    link: createSearchLink('公安机关办理刑事案件程序规定'),
  },
  {
    id: 6,
    name: '公安机关适用继续盘问规定',
    description: '关于公安机关在执法过程中适用继续盘问措施的规定。',
    link: createSearchLink('公安机关适用继续盘问规定'),
  },
  {
    id: 7,
    name: '中华人民共和国刑事诉讼法',
    description: '进行刑事诉讼必须遵守的基本法律。',
    link: createSearchLink('中华人民共和国刑事诉讼法'),
  },
  {
    id: 8,
    name: '道路交通事故处理程序规定',
    description: '公安机关交通管理部门处理道路交通事故的程序规定。',
    link: createSearchLink('道路交通事故处理程序规定'),
  },
  {
    id: 9,
    name: '中华人民共和国人民警察法',
    description: '关于人民警察的性质、任务、职责、权利和义务的法律。',
    link: createSearchLink('中华人民共和国人民警察法'),
  },
];