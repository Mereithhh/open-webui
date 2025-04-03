const innerDepsMap = {
	react: 'https://esm.sh/react@18.2.0',
	'react-dom/client': 'https://esm.sh/react-dom@18.2.0/client',
	'react-dom/': 'https://esm.sh/react-dom@18.2.0/',
	'react-dom': 'https://esm.sh/react-dom@18.2.0/',
	'lucide-react': 'https://esm.sh/lucide-react/?deps=react@18.2.0',
	'react-error-boundary': 'https://esm.sh/react-error-boundary/?deps=react@18.2.0',
	antd: 'https://esm.sh/antd?standalone&deps=react@18.2.0'
};

/**
 * 从代码中提取所有导入语句，生成importmap
 * @param code 源代码字符串
 * @returns importmap对象
 */
export function generateImportMap(code: string): { imports: Record<string, string> } {
	const imports: Record<string, string> = {
		react: 'https://esm.sh/react@18.2.0',
		'react-dom/': 'https://esm.sh/react-dom@18.2.0/',
		'react-error-boundary': 'https://esm.sh/react-error-boundary/?deps=react@18.2.0'
	};

	// 匹配import语句的正则表达式
	// 支持以下格式:
	// import pkg from 'package'
	// import { something } from 'package'
	// import * as pkg from 'package'
	const importRegex =
		/import(?:(?:(?:[ \n\t]+([^ *\n\t{},]+)[ \n\t]*(?:,|[ \n\t]+))?([ \n\t]*\{(?:[ \n\t]*[^ \n\t"'{}]+[ \n\t]*,?)+\})?[ \n\t]*)|[ \n\t]*\*[ \n\t]*as[ \n\t]+([^ \n\t{}]+)[ \n\t]+)from[ \n\t]*['"]([^'"]+)['"]|import[ \n\t]+['"]([^'"]+)['"];?/g;

	let match;
	while ((match = importRegex.exec(code)) !== null) {
		// 获取包名（从正则表达式的第4或第5个捕获组）
		const packageName = match[4] || match[5] || '';

		if (packageName) {
			// 优先使用innerDepsMap中预定义的URL
			if (packageName in innerDepsMap) {
				imports[packageName] = innerDepsMap[packageName as keyof typeof innerDepsMap];
			} else {
				// 如果包名包含react，添加react依赖
				const url = packageName.includes('react')
					? `https://esm.sh/${packageName}?deps=react@18.2.0`
					: `https://esm.sh/${packageName}`;

				imports[packageName] = url;
			}
		}
	}

	return { imports };
}
