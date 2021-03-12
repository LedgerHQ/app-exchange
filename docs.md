# Adding tests

Edit `tools/index.js` to add your coin.
Run `node tools/index.js`, it will print the variables. Copy and paste them to `common.js`.

The seed is : `glory promote mansion idle axis finger extra february uncover one trip resource lawn turtle enact monster seven myth punch hobby comfort wild raise skin`

To generate keys : [here](https://iancoleman.io/bip39/#english)

# Install yarn

First [install yarn](https://classic.yarnpkg.com/en/docs/install/#debian-stable).
`yarn install`


## Run tests

`yarn test`

To run specific tests: 
`sudo jest --runInBand --detectOpenHandles src/xrp.test.js`



